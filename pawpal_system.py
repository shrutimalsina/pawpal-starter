"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field

# Numeric rank for each priority so sorting isn't alphabetical.
PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    """A single pet care activity, like a walk or feeding."""

    description: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    time: str = ""  # optional, always two-digit "HH:MM", e.g. "08:00"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task()

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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

    def generate_plan(self) -> list[Task]:
        """Plan incomplete tasks by priority until time runs out; save the rest as skipped."""
        pending = [task for task in self.owner.get_all_tasks() if not task.completed]
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
        """Return tasks ordered by time, with tasks that have no time last."""
        return sorted(tasks, key=lambda task: (task.time == "", task.time))

    def explain_plan(self) -> str:
        """Explain why each task in self.plan was chosen and why self.skipped were not."""
        if not self.plan and not self.skipped:
            return "No tasks to schedule."

        used = sum(task.duration_minutes for task in self.plan)
        lines = [
            f"Plan for {self.owner.name}: {used} of "
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
        return "\n".join(lines)
