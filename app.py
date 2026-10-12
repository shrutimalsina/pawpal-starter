from datetime import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_ICONS = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}


def task_row(task: Task, show_status: bool = True) -> dict:
    """One table row for a task."""
    row = {
        "Time": task.time or "--",
        "Task": task.description,
        "Pet": task.pet_name,
        "Minutes": task.duration_minutes,
        "Priority": PRIORITY_ICONS.get(task.priority, task.priority),
        "Repeats": task.frequency,
    }
    if show_status:
        row["Due"] = f"{task.due_date:%b %d}"
        row["Status"] = "✅ done" if task.completed else "to do"
    return row


def task_label(task: Task) -> str:
    """Short label for picking a task from a dropdown."""
    when = f"{task.time} " if task.time else ""
    return f"{when}{task.description} ({task.pet_name}, due {task.due_date:%b %d})"


def clashing_tasks(tasks: list[Task]) -> list[Task]:
    """Return the timed tasks that overlap another task on the same day."""
    timed = [task for task in tasks if task.time]
    return [
        a for a in timed
        if any(
            b is not a and a.due_date == b.due_date
            and a.start_minutes < b.end_minutes and b.start_minutes < a.end_minutes
            for b in timed
        )
    ]

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks around the time you have each day.")

# Streamlit reruns this script on every click, so keep the Owner in session_state.
# Only create it the first time; after that, reuse the one already stored.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)

owner: Owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available today",
            min_value=0,
            max_value=1440,
            value=owner.available_minutes,
        )
    )

st.divider()

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=50, value=1)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    name = pet_name.strip()
    if not name:
        st.error("Please enter a pet name.")
    elif any(pet.name == name for pet in owner.pets):
        st.error(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name=name, species=species, age=int(age)))
        st.success(f"Added {name}!")

if owner.pets:
    st.table(
        [{"Name": pet.name, "Species": pet.species, "Age": pet.age, "Tasks": len(pet.tasks)}
         for pet in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Tasks")
if not owner.pets:
    st.info("Add a pet before adding tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            pet_choice = st.selectbox("Pet", [pet.name for pet in owner.pets])
            description = st.text_input("Task", placeholder="Morning walk")
            time_text = st.text_input("Time (optional, HH:MM)", placeholder="08:00")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        add_task = st.form_submit_button("Add task")

    if add_task:
        time_text = time_text.strip()
        try:
            # Normalize times like "8:00" to "08:00" so they sort correctly.
            time = datetime.strptime(time_text, "%H:%M").strftime("%H:%M") if time_text else ""
        except ValueError:
            time = None

        if not description.strip():
            st.error("Please enter a task description.")
        elif time is None:
            st.error("Time must look like HH:MM, for example 08:00.")
        else:
            pet = next(pet for pet in owner.pets if pet.name == pet_choice)
            pet.add_task(
                Task(
                    description=description.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    time=time,
                    frequency=frequency,
                )
            )
            st.success(f"Added {description.strip()} for {pet.name}!")

    scheduler = Scheduler(owner)

    if owner.get_all_tasks():
        # Filter with Scheduler.filter_tasks(), then show in clock order with sort_by_time().
        col1, col2 = st.columns(2)
        with col1:
            pet_filter = st.selectbox("Show pet", ["All pets"] + [pet.name for pet in owner.pets])
        with col2:
            status_filter = st.radio("Show", ["To do", "Done", "All"], horizontal=True)

        shown = scheduler.sort_by_time(
            scheduler.filter_tasks(
                pet_name=None if pet_filter == "All pets" else pet_filter,
                completed={"To do": False, "Done": True, "All": None}[status_filter],
            )
        )
        if shown:
            st.table([task_row(task) for task in shown])
        else:
            st.info("No tasks match these filters.")

        # Completing through the Scheduler adds the next daily/weekly copy automatically.
        pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
        if pending:
            with st.form("complete_task"):
                choice = st.selectbox(
                    "Mark a task as done",
                    range(len(pending)),
                    format_func=lambda i: task_label(pending[i]),
                )
                done = st.form_submit_button("Mark complete")
            if done:
                task = pending[choice]
                upcoming = scheduler.mark_task_complete(task)
                if upcoming:
                    st.session_state.flash = (
                        f"Nice! {task.description} for {task.pet_name} is done. "
                        f"The next one is due {upcoming.due_date:%a %b %d}."
                    )
                else:
                    st.session_state.flash = f"Nice! {task.description} for {task.pet_name} is done."
                st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

st.divider()

st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    st.session_state.show_schedule = True

# Keep the schedule on screen after other clicks, rebuilding it so it stays up to date.
if st.session_state.get("show_schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    if not plan and not scheduler.skipped:
        st.info("Nothing is due today. 🎉")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Tasks planned", len(plan))
        col2.metric("Time used", f"{scheduler.minutes_used} / {owner.available_minutes} min")
        if owner.available_minutes:
            st.progress(min(scheduler.minutes_used / owner.available_minutes, 1.0))

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.warning(
                f"**⚠️ {len(conflicts)} time clash(es) in today's plan.** "
                "You can't be in two places at once, so one task in each pair needs a new time:\n\n"
                + "\n".join(f"- {warning}" for warning in conflicts)
                + "\n\nTip: move the later task so it starts after the earlier one ends."
            )
        else:
            st.success("✅ No time clashes. Every task in today's plan has its own time slot.")

        if plan:
            clashing = clashing_tasks(plan)
            st.table(
                [{**task_row(task, show_status=False), "": "⚠️ clash" if task in clashing else ""}
                 for task in scheduler.sort_by_time(plan)]
            )

        if scheduler.skipped:
            st.warning(
                "**Didn't fit in today's time:** "
                + ", ".join(
                    f"{task.description} ({task.pet_name}, {task.duration_minutes} min)"
                    for task in scheduler.skipped
                )
                + ". Add more minutes above or lower another task's priority."
            )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
