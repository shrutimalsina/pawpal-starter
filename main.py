"""Temporary testing ground for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the plan as a readable table, followed by any skipped tasks."""
    print("=" * 52)
    print(f"  Today's Schedule for {scheduler.owner.name}")
    print("=" * 52)
    print(f"  {'Time':<7}{'Task':<16}{'Pet':<8}{'Min':>4}  Priority")
    print("  " + "-" * 48)

    for task in scheduler.sort_by_time(scheduler.plan):
        time = task.time or "--:--"
        print(
            f"  {time:<7}{task.description:<16}{task.pet_name:<8}"
            f"{task.duration_minutes:>4}  {task.priority}"
        )

    used = sum(task.duration_minutes for task in scheduler.plan)
    print("  " + "-" * 48)
    print(f"  Time used: {used} / {scheduler.owner.available_minutes} min")

    if scheduler.skipped:
        print("\n  Skipped (not enough time):")
        for task in scheduler.skipped:
            print(f"  - {task.description} ({task.pet_name}, {task.duration_minutes} min)")
    print()


owner = Owner("Shruti", available_minutes=90)

mochi = Pet("Mochi", "dog", age=3)
luna = Pet("Luna", "cat", age=5)
owner.add_pet(mochi)
owner.add_pet(luna)

mochi.add_task(Task("Morning walk", 30, "high", time="07:30"))
mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
mochi.add_task(Task("Bath", 45, "low", time="16:00", frequency="weekly"))
luna.add_task(Task("Feed", 5, "high", time="08:15"))
luna.add_task(Task("Brush fur", 15, "medium", time="18:00"))
luna.add_task(Task("Play time", 20, "medium"))

scheduler = Scheduler(owner)
scheduler.generate_plan()
print_schedule(scheduler)

print("Why this plan:")
print(scheduler.explain_plan())
