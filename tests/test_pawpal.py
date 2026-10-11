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
