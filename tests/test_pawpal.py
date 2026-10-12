"""Tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high", time="07:30")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high", time="08:00"))

    assert len(pet.tasks) == 1


def make_scheduler(*pets: Pet) -> Scheduler:
    owner = Owner("Shruti", available_minutes=120)
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner)


def test_sort_by_time_orders_by_clock_not_text():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Dinner", 10, time="10:00"))
    pet.add_task(Task("Play", 10))
    pet.add_task(Task("Walk", 10, time="8:00"))
    scheduler = make_scheduler(pet)

    ordered = scheduler.sort_by_time(pet.tasks)

    assert [task.description for task in ordered] == ["Walk", "Dinner", "Play"]
    assert ordered[0].time == "08:00"


def test_invalid_time_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 10, time="25:00")


def test_filter_tasks_by_pet_and_status():
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Walk", 30))
    mochi.add_task(Task("Breakfast", 10, completed=True))
    luna.add_task(Task("Feed", 5))
    scheduler = make_scheduler(mochi, luna)

    assert [t.description for t in scheduler.filter_tasks(pet_name="Mochi")] == ["Walk", "Breakfast"]
    assert [t.description for t in scheduler.filter_tasks(completed=False)] == ["Walk", "Feed"]
    assert [t.description for t in scheduler.filter_tasks(pet_name="Mochi", completed=True)] == ["Breakfast"]


@pytest.mark.parametrize("frequency, days", [("daily", 1), ("weekly", 7)])
def test_completing_recurring_task_adds_next_occurrence(frequency, days):
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, frequency=frequency, due_date=today)
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    upcoming = scheduler.mark_task_complete(task, today=today)

    assert task.completed is True
    assert upcoming.completed is False
    assert upcoming.due_date == today + timedelta(days=days)
    assert upcoming.description == "Walk" and upcoming.pet_name == "Mochi"
    assert pet.tasks == [task, upcoming]


def test_overdue_daily_task_is_next_due_tomorrow_not_in_the_past():
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, due_date=today - timedelta(days=3))
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    upcoming = scheduler.mark_task_complete(task, today=today)

    assert upcoming.due_date == date(2026, 10, 12)


def test_weekly_task_finished_early_is_next_due_a_week_after_its_due_date():
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    task = Task("Bath", 45, frequency="weekly", due_date=date(2026, 10, 18))
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    upcoming = scheduler.mark_task_complete(task, today=today)

    assert upcoming.due_date == date(2026, 10, 25)


def test_completing_same_task_twice_does_not_duplicate():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30)
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    scheduler.mark_task_complete(task)
    assert scheduler.mark_task_complete(task) is None
    assert len(pet.tasks) == 2


def test_completing_once_task_adds_nothing():
    pet = Pet("Mochi", "dog")
    task = Task("Vet visit", 60, frequency="once")
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    assert scheduler.mark_task_complete(task) is None
    assert len(pet.tasks) == 1


def test_generate_plan_skips_tasks_not_yet_due():
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, due_date=today))
    pet.add_task(Task("Bath", 45, frequency="weekly", due_date=today + timedelta(days=7)))
    scheduler = make_scheduler(pet)

    plan = scheduler.generate_plan(today=today)

    assert [task.description for task in plan] == ["Walk"]
    assert scheduler.skipped == []


def test_detect_conflicts_flags_same_start_time():
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Breakfast", 10, time="08:00"))
    luna.add_task(Task("Feed", 5, time="08:00"))
    scheduler = make_scheduler(mochi, luna)

    assert len(scheduler.detect_conflicts(scheduler.owner.get_all_tasks())) == 1


def test_detect_conflicts_flags_overlap():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, time="07:30"))
    pet.add_task(Task("Breakfast", 10, time="07:45"))
    scheduler = make_scheduler(pet)

    warnings = scheduler.detect_conflicts(pet.tasks)

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Breakfast" in warnings[0]


def test_detect_conflicts_allows_back_to_back_tasks():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, time="07:30"))
    pet.add_task(Task("Breakfast", 10, time="08:00"))
    pet.add_task(Task("Play", 20))  # no time, never conflicts
    scheduler = make_scheduler(pet)

    assert scheduler.detect_conflicts(pet.tasks) == []


def test_detect_conflicts_catches_long_task_overlapping_several():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Hike", 120, time="07:00"))
    pet.add_task(Task("Breakfast", 10, time="07:30"))
    pet.add_task(Task("Meds", 5, time="08:30"))
    scheduler = make_scheduler(pet)

    assert len(scheduler.detect_conflicts(pet.tasks)) == 2


def test_detect_conflicts_same_time_same_pet_message():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Breakfast", 10, time="08:00"))
    pet.add_task(Task("Meds", 5, time="08:00"))
    scheduler = make_scheduler(pet)

    assert scheduler.detect_conflicts(pet.tasks) == [
        "Same time (both for Mochi): Breakfast 08:00-08:10 and Meds at 08:00"
    ]


def test_detect_conflicts_ignores_tasks_on_different_days():
    pet = Pet("Mochi", "dog")
    walk = Task("Walk", 30, time="07:30")
    pet.add_task(walk)
    scheduler = make_scheduler(pet)
    scheduler.mark_task_complete(walk)  # adds tomorrow's 07:30 walk

    assert scheduler.detect_conflicts(pet.tasks) == []


# --- Sorting ---


def test_sort_by_time_returns_chronological_order():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Dinner", 10, time="18:00"))
    pet.add_task(Task("Lunch", 10, time="12:30"))
    pet.add_task(Task("Walk", 30, time="07:30"))
    pet.add_task(Task("Midnight snack", 5, time="00:00"))
    scheduler = make_scheduler(pet)

    ordered = scheduler.sort_by_time(pet.tasks)

    assert [task.time for task in ordered] == ["00:00", "07:30", "12:30", "18:00"]


def test_sort_by_time_keeps_added_order_for_same_time():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Breakfast", 10, time="08:00"))
    pet.add_task(Task("Meds", 5, time="08:00"))
    scheduler = make_scheduler(pet)

    assert [task.description for task in scheduler.sort_by_time(pet.tasks)] == ["Breakfast", "Meds"]


def test_sort_by_priority_high_first_and_shorter_first_on_ties():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Bath", 45, "low"))
    pet.add_task(Task("Walk", 30, "high"))
    pet.add_task(Task("Brush", 15, "medium"))
    pet.add_task(Task("Feed", 5, "high"))
    pet.add_task(Task("Typo", 5, "High"))  # unknown priority sorts last
    scheduler = make_scheduler(pet)

    ordered = scheduler.sort_by_priority(pet.tasks)

    assert [task.description for task in ordered] == ["Feed", "Walk", "Brush", "Bath", "Typo"]


# --- Building the plan ---


def test_generate_plan_picks_high_priority_first_within_time():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Bath", 45, "low"))
    pet.add_task(Task("Walk", 30, "high"))
    pet.add_task(Task("Brush", 15, "medium"))
    owner = Owner("Shruti", available_minutes=50)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan()

    assert [task.description for task in plan] == ["Walk", "Brush"]
    assert [task.description for task in scheduler.skipped] == ["Bath"]
    assert scheduler.minutes_used == 45


def test_generate_plan_fits_smaller_task_after_skipping_big_one():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, "high"))
    pet.add_task(Task("Grooming", 40, "medium"))
    pet.add_task(Task("Feed", 10, "low"))
    owner = Owner("Shruti", available_minutes=40)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan()

    assert [task.description for task in plan] == ["Walk", "Feed"]
    assert [task.description for task in scheduler.skipped] == ["Grooming"]


def test_generate_plan_includes_task_that_exactly_fits():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, "high"))
    owner = Owner("Shruti", available_minutes=30)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    assert [task.description for task in scheduler.generate_plan()] == ["Walk"]


def test_generate_plan_leaves_out_completed_tasks():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, completed=True))
    pet.add_task(Task("Feed", 5))
    scheduler = make_scheduler(pet)

    plan = scheduler.generate_plan()

    assert [task.description for task in plan] == ["Feed"]
    assert scheduler.skipped == []


def test_generate_plan_with_no_time_skips_everything():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30))
    owner = Owner("Shruti", available_minutes=0)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan() == []
    assert [task.description for task in scheduler.skipped] == ["Walk"]


def test_pet_with_no_tasks_gives_empty_plan():
    scheduler = make_scheduler(Pet("Mochi", "dog"))

    assert scheduler.generate_plan() == []
    assert scheduler.explain_plan() == "No tasks to schedule."
    assert scheduler.filter_tasks(pet_name="Mochi") == []


def test_owner_with_no_pets_gives_empty_plan():
    scheduler = make_scheduler()

    assert scheduler.generate_plan() == []
    assert scheduler.filter_tasks(pet_name="Rex") == []


# --- Recurring tasks ---


def test_completing_daily_task_creates_task_for_next_day():
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, "high", time="07:30", due_date=today)
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    upcoming = scheduler.mark_task_complete(task, today=today)

    assert upcoming in pet.tasks
    assert upcoming.due_date == date(2026, 10, 12)
    assert upcoming.time == "07:30" and upcoming.priority == "high"
    assert upcoming.completed is False


def test_recurring_task_rolls_over_end_of_year():
    today = date(2026, 12, 31)
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, due_date=today)
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    assert scheduler.mark_task_complete(task, today=today).due_date == date(2027, 1, 1)


def test_new_daily_task_shows_up_in_tomorrows_plan_not_todays():
    today = date(2026, 10, 11)
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, due_date=today)
    pet.add_task(task)
    scheduler = make_scheduler(pet)
    scheduler.mark_task_complete(task, today=today)

    assert scheduler.generate_plan(today=today) == []
    assert len(scheduler.generate_plan(today=today + timedelta(days=1))) == 1


# --- Conflict detection ---


def test_detect_conflicts_flags_duplicate_times_across_pets():
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Breakfast", 10, time="08:00"))
    luna.add_task(Task("Feed", 5, time="08:00"))
    scheduler = make_scheduler(mochi, luna)

    assert scheduler.detect_conflicts(scheduler.owner.get_all_tasks()) == [
        "Same time (Mochi and Luna): Breakfast 08:00-08:10 and Feed at 08:00"
    ]


def test_detect_conflicts_with_no_timed_tasks_returns_empty():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Play", 20))
    scheduler = make_scheduler(pet)

    assert scheduler.detect_conflicts([]) == []
    assert scheduler.detect_conflicts(pet.tasks) == []
