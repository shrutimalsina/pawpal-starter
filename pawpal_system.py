"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Numeric rank for each priority so sorting isn't alphabetical.
PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}

# Days until the next occurrence of a recurring task. "once" is not listed.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


def _to_minutes(time: str) -> int:
    """Convert "H:MM" or "HH:MM" to minutes after midnight, e.g. "8:00" -> 480."""
    try:
        hours, minutes = (int(part) for part in time.split(":"))
    except ValueError:
        raise ValueError(f"Time must look like HH:MM, got {time!r}") from None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"Time out of range: {time!r}")
    return hours * 60 + minutes


def _format_minutes(total: int) -> str:
    """Convert minutes after midnight back to "HH:MM"."""
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class Task:
    """A single pet care activity, like a walk or feeding."""

    description: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    time: str = ""  # optional, normalized to two-digit "HH:MM", e.g. "08:00"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task()
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate the time and normalize it, so "8:00" is stored as "08:00"."""
        if self.time:
            self.time = _format_minutes(_to_minutes(self.time))

    @property
    def start_minutes(self) -> int | None:
        """Start time in minutes after midnight, or None if the task has no time."""
        return _to_minutes(self.time) if self.time else None

    @property
    def end_minutes(self) -> int | None:
        """End time in minutes after midnight, or None if the task has no time."""
        start = self.start_minutes
        return None if start is None else start + self.duration_minutes

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self, today: date | None = None) -> "Task | None":
        """Return a copy of this task for its next due date, or None if it doesn't repeat.

        The new due date is counted from whichever is later, today or the old
        due date. A task finished late doesn't come back already overdue, and a
        task finished early doesn't come back due on the same day it was:
        "daily" -> +1 day, "weekly" -> +7 days, "once" -> None.
        The copy keeps every other field (description, pet, time, priority)
        and starts as not completed. Pass `today` to use a fixed date in tests.
        """
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        start = max(today or date.today(), self.due_date)
        return replace(self, completed=False, due_date=start + timedelta(days=days))


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and set the task's pet_name."""
        task.pet_name = self.name
        self.tasks.append(task)


@dataclass
class Owner:
    """A pet owner with limited time each day for pet care."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily care plan that fits the owner's available time."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    @property
    def minutes_used(self) -> int:
        """Total minutes taken by the tasks in the current plan."""
        return sum(task.duration_minutes for task in self.plan)

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return the owner's tasks that match every filter given.

        Leaving a filter as None means "don't filter on this", so one method
        covers all combinations:
            filter_tasks(pet_name="Luna")                    # one pet
            filter_tasks(completed=False)                    # still to do
            filter_tasks(pet_name="Mochi", completed=True)   # both
        """
        return [
            task
            for task in self.owner.get_all_tasks()
            if (pet_name is None or task.pet_name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def generate_plan(self, today: date | None = None) -> list[Task]:
        """Build today's plan and return it; tasks that don't fit go in self.skipped.

        Only tasks that are not completed and are due today or earlier are
        considered. They are taken from highest to lowest priority (shorter
        first on ties) and added while they fit in the owner's minutes left.
        A task that doesn't fit is skipped, but later smaller tasks can still fit.
        """
        today = today or date.today()
        pending = [task for task in self.filter_tasks(completed=False) if task.due_date <= today]
        self.plan = []
        self.skipped = []
        minutes_left = self.owner.available_minutes

        for task in self.sort_by_priority(pending):
            if task.duration_minutes <= minutes_left:
                self.plan.append(task)
                minutes_left -= task.duration_minutes
            else:
                self.skipped.append(task)

        return self.plan

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks from high to low priority, shorter tasks first on ties."""
        return sorted(
            tasks,
            key=lambda task: (-PRIORITY_ORDER.get(task.priority, 0), task.duration_minutes),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by clock time, with tasks that have no time last.

        The sort key is a pair: (has no time?, start in minutes). False sorts
        before True, so timed tasks come first, and comparing minutes as numbers
        keeps "8:00" (480) before "10:00" (600). Tasks at the same time keep the
        order they were in.
        """
        return sorted(tasks, key=lambda task: (not task.time, task.start_minutes or 0))

    def mark_task_complete(self, task: Task, today: date | None = None) -> Task | None:
        """Mark a task done and, if it repeats, add its next occurrence to the same pet.

        Returns the new task, or None for a "once" task. The finished task stays
        in the pet's list (marked done) as a record. Completing an
        already-completed task does nothing, so no duplicate copy is made.
        """
        if task.completed:
            return None
        task.mark_complete()
        upcoming = task.next_occurrence(today)
        if upcoming is not None:
            pet = next(pet for pet in self.owner.pets if pet.name == task.pet_name)
            pet.add_task(upcoming)
        return upcoming

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for each timed task that starts before an earlier one ends.

        Lightweight: one pass over the tasks sorted by (due date, start time),
        remembering the task that ends latest. It never raises; callers decide
        what to do with the warnings. Defaults to the current plan, checks across
        all pets (the owner can't do two things at once), only compares tasks due
        on the same day, and ignores tasks without a time.
        """
        timed = sorted(
            (task for task in (self.plan if tasks is None else tasks) if task.time),
            key=lambda task: (task.due_date, task.start_minutes),
        )
        warnings = []
        latest = None  # the task seen so far that ends last on the current day
        for task in timed:
            if latest is not None and latest.due_date != task.due_date:
                latest = None  # new day, nothing carries over
            if latest is not None and task.start_minutes < latest.end_minutes:
                warnings.append(self._conflict_message(latest, task))
            if latest is None or task.end_minutes > latest.end_minutes:
                latest = task
        return warnings

    @staticmethod
    def _conflict_message(first: Task, second: Task) -> str:
        """Describe a clash between two tasks, e.g. same time vs overlap, same pet vs two pets."""
        kind = "Same time" if first.time == second.time else "Overlap"
        who = (f"both for {first.pet_name}" if first.pet_name == second.pet_name
               else f"{first.pet_name} and {second.pet_name}")
        return (
            f"{kind} ({who}): {first.description} {first.time}-"
            f"{_format_minutes(first.end_minutes)} and {second.description} at {second.time}"
        )

    def explain_plan(self) -> str:
        """Explain why each task in self.plan was chosen and why self.skipped were not."""
        if not self.plan and not self.skipped:
            return "No tasks to schedule."

        lines = [
            f"Plan for {self.owner.name}: {self.minutes_used} of "
            f"{self.owner.available_minutes} minutes used."
        ]
        for task in self.sort_by_time(self.plan):
            when = f"{task.time} " if task.time else ""
            lines.append(
                f"- {when}{task.description} ({task.pet_name}, {task.duration_minutes} min): "
                f"chosen because it is {task.priority} priority and fit in the time left."
            )
        for task in self.skipped:
            lines.append(
                f"- Skipped {task.description} ({task.pet_name}, {task.duration_minutes} min): "
                f"not enough time left after higher priority tasks."
            )
        for warning in self.detect_conflicts():
            lines.append(f"- Conflict: {warning}")
        return "\n".join(lines)
