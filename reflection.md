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

-My scheduler looks at:
1) Time: how many minutes the owner has for pet care that day. The plan can never go over this.
2) Priority: high, medium, or low. Higher priority tasks get picked first.
3) Duration: if two tasks have the same priority, the shorter one goes first so more tasks can fit.
4) Status and due date: tasks that are already done, or not due until a later day (like a weekly bath), are left out of today's plan.
5) Task times: these are used to put the plan in clock order and to warn the owner when two tasks overlap.

- How did you decide which constraints mattered most?

-I made the owner's time the hard limit, because no matter how important a task is, the owner can't do more than the time they have. After that, priority mattered most, because things like feeding and meds are more important than a bath or brushing, so if something has to be dropped, it should be the less important task. Overlapping times only give a warning and don't change the plan, because I think the owner knows their day better than the app does and should decide what to move.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

-My conflict check does not compare every task with every other task. Instead, it puts the day's tasks in time order and goes through them once, keeping track of the task that ends the latest so far. If the next task starts before that task ends, it shows a warning. This means it does catch overlapping tasks, not just ones at the exact same time (for example, a 30 minute walk at 07:30 and feeding at 07:45). But it can miss reporting some pairs. For example, if Mochi has a 2 hour hike at 07:00, and there's breakfast at 07:30 and meds at 07:35, I get a warning for the hike and breakfast, and for the hike and meds, but not a separate one saying breakfast and meds also clash with each other.

- Why is that tradeoff reasonable for this scenario?

-I think this is reasonable because every task that clashes still gets flagged at least once, so the owner will still notice it and fix it. A pet owner only has a handful of tasks in a day, so they don't need a full list of every single pair that clashes, they just need to know which tasks to move. It also keeps the code simple and easy to follow. The check also only gives a warning instead of crashing or moving tasks around on its own, so the owner gets to decide what to change.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

-I used AI in almost every phase: brainstorming the classes and drawing the first UML diagram, turning the UML into a class skeleton, filling in the logic, planning and writing tests, connecting the logic to the Streamlit app, and updating the README and final UML at the end.

- Which AI coding assistant features were most effective for building your scheduler?

-The features that helped the most were:
1) Agent mode / automatic editing: the AI could change several files at once, so when I changed a class in pawpal_system.py, it also updated the UML diagram and README so everything stayed matching.
2) Asking it to review my code: when I asked it to look at my skeleton for "missing relationships or logic bottlenecks", it found real problems before I wrote any logic, like tasks not knowing which pet they belonged to and priorities sorting in alphabetical order.
3) Running things in the terminal: it ran main.py and the pytest tests itself after making changes, so I could see right away that the code actually worked instead of just trusting it.
4) Planning tests: asking it to list the happy paths and edge cases first (like a pet with no tasks, or two tasks at the same time) made it much easier to write tests that covered more than just the obvious cases.

- How did using separate chat sessions for different phases help you stay organized?

-I used separate chat sessions for design planning, implementation, and testing. This kept each conversation focused on one job, so the AI wasn't mixing up old ideas from the design phase with the code I actually had later. It also made it easier for me to go back and find what I decided in each phase, and starting a new session meant the AI had to look at my current files instead of remembering an older version of them.

- What kinds of prompts or questions were most helpful?

-The most helpful prompts were specific ones that asked the AI to check or explain something, like "review this skeleton for missing relationships", "what edge cases should I test for sorting and recurring tasks", or "how should a conflict warning be shown to a pet owner". Telling it to keep things simple and not too complicated also helped, because otherwise it tended to add more than I needed.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

-One example was the recurring task logic. The first version that came from the AI counted the next due date from today, so a daily task finished late wouldn't come back already overdue. That sounded right at first, but later, when the AI ran main.py to put the output in my README, it pointed out that Mochi's weekly bath showed up twice on the same date. The bath was due Oct 18, it was marked done early on Oct 11, and the next bath was also due Oct 18, because today + 7 days was Oct 18. This happens because next_occurrence() counts from today, not from the old due date. I checked the output myself to confirm it, and then decided to change it to count from whichever date is later, today or the task's due date. That keeps the "finished late doesn't come back overdue" behavior and also handles early completions, so now the next bath is due Oct 25.

- Which AI suggestion did you reject or modify to keep your system design clean?

-Besides the recurring task fix, I also didn't keep every method the AI suggested. For example, my first UML had a get_tasks() method on Pet, but it did the same thing as just reading the tasks list, so I removed it to keep the classes simple. I also chose to keep conflict detection as just a warning instead of having the scheduler move tasks around on its own, because that would make the Scheduler much more complicated and take the decision away from the owner.

- How did you evaluate or verify what the AI suggested?

-I didn't just trust the code because it looked right. I ran main.py and read the output, and when the AI pointed out the double bath, I looked at the dates myself to make sure it was really a bug before changing anything. I also ran the tests with python -m pytest after every change, and for the bath bug I added a new test (a weekly task finished early should be due a week after its due date) so the bug can't come back without a test failing. For the Streamlit app, I clicked through it myself to check that adding pets, adding tasks, and generating the schedule actually worked.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

-I have 33 tests that cover:
1) Sorting: tasks come out in clock order (8:00 before 10:00), tasks with no time go last, and priorities go high, medium, low.
2) Building the plan: high priority tasks get picked first, the plan never goes over the owner's time, a smaller task can still fit after a big one is skipped, and completed or not-yet-due tasks are left out.
3) Recurring tasks: finishing a daily task adds one for tomorrow, a weekly task adds one a week later, "once" tasks don't repeat, and the date works across the end of the year (Dec 31 to Jan 1).
4) Conflicts: tasks at the same time or overlapping times get flagged, but back-to-back tasks and tasks on different days don't.
5) Edge cases: a pet with no tasks, an owner with no pets, 0 minutes available, and invalid times like "25:00".

- Why were these tests important?

-These are the main things the scheduler is supposed to do, so if any of them broke, the app would give the owner a wrong plan. The edge case tests were important because those are the situations I wouldn't normally try by hand, and they're where bugs usually hide. The tests also let me change code (like the recurring task fix) without being scared of breaking something else, because I could just run them again.

**b. Confidence**

- How confident are you that your scheduler works correctly?

-I'd say 4 out of 5. All 33 tests pass and they cover the main features plus a lot of edge cases, and the main.py output and the app both look right when I check them. I'm not giving it 5 because there are still a few cases I know aren't handled yet.

- What edge cases would you test next if you had more time?

-Next I would test:
1) A task with a duration of 0 or a negative number, which the code doesn't stop right now.
2) A task that goes past midnight (like 23:30 for an hour) and whether it clashes with an early task the next day.
3) Two pets with the same name, since the scheduler finds a pet by its name.
4) The Streamlit app itself, like making sure the right messages show up when a form has bad input.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

-I'm most satisfied with how the conflict warnings and the plan explanation turned out. Instead of just showing a list of tasks, the app tells the owner which tasks clash, for which pets, and what to do about it, and it explains why each task was picked or skipped. I'm also happy that the design stayed simple with just four classes, even after adding sorting, filtering, recurring tasks, and conflicts.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

-If I had more time, I would:
1) Let the user edit or delete a task in the app, not just add and complete them.
2) Save the data so it doesn't disappear when the page is refreshed.
3) Add owner preferences, like preferred times of day for walks.
4) Have detect_conflicts() return the tasks that clash and not just the warning messages, so the app doesn't need its own separate overlap check to mark the clashing rows.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

-The biggest thing I learned is that the AI is really fast at writing code, but I still have to be the one who decides what the system should look like and checks that it's right. The AI can write a lot of code that looks correct and even passes tests, like the recurring task logic, and that bug was only found by looking at the real output, not the tests. The AI pointed it out, but it was still my job to check it and decide how the fix should work. Being the "lead architect" meant starting with my own design (the UML), asking the AI to review it instead of just accepting whatever it gave me, keeping things simple when it wanted to add more, and always verifying with tests and real output. I learned that AI works best as a helper that I guide with clear questions, not something I hand the whole project to.
