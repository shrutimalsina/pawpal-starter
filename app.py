from datetime import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

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

    tasks = owner.get_all_tasks()
    if tasks:
        st.table(
            [{"Pet": task.pet_name, "Task": task.description, "Time": task.time or "--",
              "Minutes": task.duration_minutes, "Priority": task.priority,
              "Frequency": task.frequency}
             for task in tasks]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    if not plan and not scheduler.skipped:
        st.info("No tasks to schedule yet.")
    else:
        st.metric("Time used", f"{scheduler.minutes_used} / {owner.available_minutes} min")

        for warning in scheduler.detect_conflicts():
            st.warning(f"Overlapping tasks: {warning}")

        if plan:
            st.table(
                [{"Time": task.time or "--", "Task": task.description, "Pet": task.pet_name,
                  "Minutes": task.duration_minutes, "Priority": task.priority}
                 for task in scheduler.sort_by_time(plan)]
            )
        if scheduler.skipped:
            st.warning(
                "Skipped (not enough time): "
                + ", ".join(f"{task.description} ({task.pet_name})" for task in scheduler.skipped)
            )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
