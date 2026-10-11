"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity, like a walk or feeding."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    time: str = ""  # optional, e.g. "08:00"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass


@dataclass
class Owner:
    """A pet owner with limited time each day for pet care."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Builds a daily care plan that fits the owner's available time."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> list[Task]:
        """Pick tasks by priority until the owner's available minutes run out."""
        pass

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from high to low priority."""
        pass

    def explain_plan(self) -> str:
        """Explain why each task was included in the plan."""
        pass
