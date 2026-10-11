"""Temporary testing ground for the PawPal+ logic layer."""

from datetime import date, timedelta

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

    print("  " + "-" * 48)
    print(f"  Time used: {scheduler.minutes_used} / {scheduler.owner.available_minutes} min")

    if scheduler.skipped:
        print("\n  Skipped (not enough time):")
        for task in scheduler.skipped:
            print(f"  - {task.description} ({task.pet_name}, {task.duration_minutes} min)")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print("\n  Warning, overlapping tasks:")
        for warning in conflicts:
            print(f"  ! {warning}")
    print()


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a titled list of tasks, one per line."""
    print(f"\n{title}")
    for task in tasks:
        status = "done" if task.completed else "todo"
        print(f"  {task.time or '--:--'}  {task.description:<14}{task.pet_name:<7}"
              f"{status}  due {task.due_date}")


owner = Owner("Shruti", available_minutes=90)

mochi = Pet("Mochi", "dog", age=3)
luna = Pet("Luna", "cat", age=5)
owner.add_pet(mochi)
owner.add_pet(luna)

# Added out of time order on purpose; "7:45" also tests unpadded times.
luna.add_task(Task("Brush fur", 15, "medium", time="18:00"))
mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
mochi.add_task(Task("Morning walk", 30, "high", time="07:30"))
luna.add_task(Task("Feed", 5, "high", time="7:45"))  # clashes with the walk
luna.add_task(Task("Play time", 20, "medium"))
# Weekly bath was last done today, so it isn't due again until next week.
mochi.add_task(Task("Bath", 45, "low", time="16:00", frequency="weekly",
                    due_date=date.today() + timedelta(days=7)))

scheduler = Scheduler(owner)
scheduler.generate_plan()
print_schedule(scheduler)

print("Why this plan:")
print(scheduler.explain_plan())

print("\n--- Conflict detection ---")
mochi.add_task(Task("Meds", 5, "high", time="08:00"))            # same time, same pet as Breakfast
mochi.add_task(Task("Evening walk", 20, "medium", time="18:00"))  # same time as Luna's Brush fur
todays_tasks = [task for task in scheduler.filter_tasks(completed=False)
                if task.due_date <= date.today()]
conflicts = scheduler.detect_conflicts(todays_tasks)
if conflicts:
    print(f"Found {len(conflicts)} conflict(s) in today's tasks:")
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("No conflicts today.")

print("\n--- Recurring tasks ---")
luna.add_task(Task("Vet checkup", 60, "high", frequency="once"))
for name in ["Morning walk", "Bath", "Vet checkup"]:
    task = next(task for task in owner.get_all_tasks() if task.description == name)
    upcoming = scheduler.mark_task_complete(task)
    if upcoming:
        print(f"Completed {name} ({task.frequency}): next one is due {upcoming.due_date}.")
    else:
        print(f"Completed {name} ({task.frequency}): no repeat.")


print("\n--- Sorting and filtering ---")
print_tasks("All tasks, in the order they were added:", owner.get_all_tasks())
print_tasks("All tasks, sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()))
print_tasks("Luna's tasks, sorted by time:",
            scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna")))
print_tasks("Completed tasks:", scheduler.filter_tasks(completed=True))
print_tasks("Mochi's pending tasks:", scheduler.filter_tasks(pet_name="Mochi", completed=False))
