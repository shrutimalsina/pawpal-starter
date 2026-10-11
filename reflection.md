# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

-So, the user should be able to: 
1) Add their and their pets information.(For the owner it could be their: job, commitment. And for the pets, this could include species, breed, and age)
2) See the daily activities (like feeding, walking, grooming, bathing) they need to complete along with their priority levels and be able to edit them.
3) Generate and view a detailed daily plan with an explanation answer why the system chose that plan to care for their pets.


- Briefly describe your initial UML design.

-My initial UML design has four classes: Owner, Pet, Task, and Scheduler. An owner can have many pets, each pet can have many tasks, and the scheduler looks at the owner to build the daily plan. I tried to keep the attributes simple so the design doesn't get too complicated.

- What classes did you include, and what responsibilities did you assign to each?

-So, the classes I included are:
1) Owner: stores the owner's name, how many minutes they have in a day for pet care, and their list of pets. It can add a new pet and get all the tasks from all of their pets in one list.
2) Pet: stores the pet's name, species, age, and its own list of tasks. It can add a new task for that pet.
3) Task: one care activity like feeding or walking. It stores the description, how long it takes, its priority (low, medium, high), an optional time, how often it happens (once, daily, or weekly), and whether it's done or not. It can be marked as complete.
4) Scheduler: this is the "brain" of the app. It takes the owner, sorts their tasks by priority, picks tasks until the owner runs out of time, and explains why it chose that plan.

**b. Design changes**

- Did your design change during implementation?

-Yes, my design changed a little after I asked AI to review my UML diagram and class skeleton for missing relationships and possible problems.

- If yes, describe at least one change and why you made it.

-The changes I made were:
1) I removed the get_tasks() method from Pet because the tasks list can already be accessed directly, so the method wasn't doing anything extra.
2) I added a pet_name to Task. Before, when the owner got all the tasks in one list, there was no way to tell which pet a task was for (for example, if two pets both had a "Walk" task).
3) I gave the Scheduler a plan list and a skipped list. Before, the explain_plan() method had no way to see the plan it was supposed to explain, and it couldn't say why some tasks were left out.
4) I added a number for each priority (high = 3, medium = 2, low = 1). Sorting the words "high", "medium", "low" would put them in alphabetical order, which is wrong.
5) I decided the scheduler should skip tasks that are already completed, and that times should always be written like "08:00" so they sort correctly. I also added a sort_by_time() method for this.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
