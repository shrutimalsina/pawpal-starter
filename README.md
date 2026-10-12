# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running `python main.py` (owner with 90 minutes available, two pets, tasks added out of time order on purpose). Mochi's weekly Bath isn't due until next week, so it isn't in today's plan:

```
====================================================
  Today's Schedule for Shruti
====================================================
  Time   Task            Pet      Min  Priority
  ------------------------------------------------
  07:30  Morning walk    Mochi     30  high
  07:45  Feed            Luna       5  high
  08:00  Breakfast       Mochi     10  high
  18:00  Brush fur       Luna      15  medium
  --:--  Play time       Luna      20  medium
  ------------------------------------------------
  Time used: 80 / 90 min

  Warning, overlapping tasks:
  ! Overlap (Mochi and Luna): Morning walk 07:30-08:00 and Feed at 07:45

Why this plan:
Plan for Shruti: 80 of 90 minutes used.
- 07:30 Morning walk (Mochi, 30 min): chosen because it is high priority and fit in the time left.
- 07:45 Feed (Luna, 5 min): chosen because it is high priority and fit in the time left.
- 08:00 Breakfast (Mochi, 10 min): chosen because it is high priority and fit in the time left.
- 18:00 Brush fur (Luna, 15 min): chosen because it is medium priority and fit in the time left.
- Play time (Luna, 20 min): chosen because it is medium priority and fit in the time left.
- Conflict: Overlap (Mochi and Luna): Morning walk 07:30-08:00 and Feed at 07:45

--- Conflict detection ---
Found 3 conflict(s) in today's tasks:
  WARNING: Overlap (Mochi and Luna): Morning walk 07:30-08:00 and Feed at 07:45
  WARNING: Same time (both for Mochi): Breakfast 08:00-08:10 and Meds at 08:00
  WARNING: Same time (Mochi and Luna): Evening walk 18:00-18:20 and Brush fur at 18:00

--- Recurring tasks ---
Completed Morning walk (daily): next one is due 2026-10-12.
Completed Bath (weekly): next one is due 2026-10-18.
Completed Vet checkup (once): no repeat.
```

## 🧪 Testing PawPal+

Run the full test suite from the project folder (with the virtual environment active):

```bash
python -m pytest
```

### What the tests cover

The 32 tests in `tests/test_pawpal.py` check both normal use ("happy paths") and edge cases:

- **Sorting:** tasks come back in clock order (`"8:00"` before `"10:00"`, `"00:00"` first), tasks with no time go last, and tasks at the same time keep the order they were added. Priority sorting goes high → medium → low, with shorter tasks first on ties and unknown priorities last.
- **Building the plan:** high priority tasks are picked first within the owner's time, a smaller task can still fit after a big one is skipped, a task that exactly fills the time is included, and completed or not-yet-due tasks are left out. Edge cases include 0 minutes available, a pet with no tasks, and an owner with no pets.
- **Recurring tasks:** completing a daily task adds a new one for the next day (weekly adds one 7 days later), keeping the same time and priority. "Once" tasks don't repeat, completing a task twice doesn't make a duplicate, late tasks don't come back overdue, and Dec 31 rolls over to Jan 1.
- **Conflict detection:** tasks at the exact same time or overlapping times are flagged, for the same pet or across pets. Back-to-back tasks, tasks on different days, and tasks with no time are not flagged.
- **Basics:** marking a task complete, adding tasks to a pet, filtering by pet and status, and rejecting invalid times like `"25:00"`.

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/shrutitimalsina/Desktop/AI Engineering/Project2/pawpal-starter
plugins: anyio-4.15.1
collected 32 items

tests/test_pawpal.py ................................                    [100%]

============================== 32 passed in 0.02s ==============================
```

### Confidence level

⭐⭐⭐⭐☆ (4/5)

All 32 tests pass, and they cover the scheduler's main jobs (sorting, choosing tasks within the time limit, recurring tasks, and conflict warnings) along with the edge cases I could think of. I'm not giving it 5 stars because a few cases aren't handled yet: a task's duration can be 0 or negative, a task that runs past midnight isn't checked against the next day's tasks, and the Streamlit UI itself isn't covered by automated tests.

## 📐 Smarter Scheduling

All of this logic lives in `pawpal_system.py`. Run `python main.py` to see each feature print in the terminal.

| Feature | Method(s) | What it does |
|---------|-----------|--------------|
| Sorting by time | `Scheduler.sort_by_time()` | Puts tasks in clock order, with tasks that have no time at the end |
| Sorting by priority | `Scheduler.sort_by_priority()` | High before medium before low, shorter tasks first on ties |
| Filtering | `Scheduler.filter_tasks()` | Shows tasks for one pet, by done / not done, or both |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns when tasks overlap, for the same pet or different pets |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a daily or weekly task adds the next one automatically |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** sorts tasks by their start time. Times are turned into minutes after midnight before comparing (`"07:45"` becomes 465). This means `"8:00"` correctly comes before `"10:00"`, which wouldn't happen if the times were compared as plain text. Tasks with no time go last.
- When a task is created, its time is checked and tidied up: `"8:00"` is saved as `"08:00"`, and a time like `"25:00"` is rejected with an error right away.
- **`Scheduler.sort_by_priority(tasks)`** is what `generate_plan()` uses to choose tasks: highest priority first, and the shorter task first when two have the same priority.

### Filtering

- **`Scheduler.filter_tasks(pet_name=None, completed=None)`** returns the owner's tasks that match the filters you give it. Anything left as `None` isn't filtered on:

  ```python
  scheduler.filter_tasks(pet_name="Luna")                   # all of Luna's tasks
  scheduler.filter_tasks(completed=False)                   # everything still to do
  scheduler.filter_tasks(pet_name="Mochi", completed=True)  # what Mochi has had done
  ```
- Filters and sorting can be combined, e.g. `sort_by_time(filter_tasks(pet_name="Luna"))`.
- **`Scheduler.generate_plan()`** uses filtering too: it only plans tasks that aren't done yet and are due today or earlier.

### Conflict detection

- **`Scheduler.detect_conflicts(tasks=None)`** checks the plan (or any list of tasks you pass in) for tasks that clash. It returns a list of warning messages and never crashes the program. An empty list means no clashes.
- How it works: it puts the tasks in time order and goes through them once, keeping track of the task that ends the latest so far. If the next task starts before that one ends, it adds a warning.
- It catches **overlaps**, not only exact matches. A 30 minute walk at 07:30 clashes with feeding at 07:45. Back-to-back tasks (a walk 07:30-08:00, then breakfast at 08:00) are fine.
- It checks **across pets**, because the owner can't be in two places at once. It only compares tasks due on the **same day**, and skips tasks with no time.
- Each message says what kind of clash it is:
  ```
  Same time (both for Mochi): Breakfast 08:00-08:10 and Meds at 08:00
  Overlap (Mochi and Luna): Morning walk 07:30-08:00 and Feed at 07:45
  ```
- The warnings show in the terminal, at the end of `explain_plan()`, and in the Streamlit app.
- Tradeoff: each task is compared with the latest-ending task, not with every other task. Every clashing task still gets flagged at least once (see `reflection.md`, section 2b).

### Recurring tasks

- Each `Task` has a `frequency` (`"once"`, `"daily"`, or `"weekly"`) and a `due_date`.
- **`Scheduler.mark_task_complete(task)`** marks the task done. If it repeats, it calls **`Task.next_occurrence()`** and adds the new copy to the same pet:
  - `"daily"`: due today + 1 day
  - `"weekly"`: due today + 7 days
  - `"once"`: nothing is added
- The next date is worked out with Python's `timedelta`, so it handles the end of a month or year correctly. It's counted from **today**, so a task finished late doesn't come back already overdue.
- The finished task stays in the list marked as done, so you can still see what was completed. Completing the same task twice doesn't make a second copy.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
