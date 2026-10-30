# Usability test - BL-31 (MPMS-NF-003)

**Requirement:** a new user can create a project and assign a task within
**10 minutes**.
**Acceptance:** **5 of 5** test users succeed.

## What counts as success
A participant succeeds only if **all three** are true:

1. They finish the task card below **in 10 minutes or less** (timer starts
   when they begin reading the card, stops when the task is visible on the
   project page with the teammate's name as assignee).
2. They did it **without help**. The facilitator may say "please keep going"
   but may not point at buttons, read labels aloud, or explain the screens.
   A hint means the trial is recorded as **not successful**.
3. The result is correct: the project exists, the task exists in it and it is
   assigned to the teammate.

The test passes only when **5 of 5** participants succeed.

## Participants
Five people who have **never used MPMS** (not on the project team). A mix of
technical and non-technical people is better than five classmates.

## Setup (before the first participant)
1. Start with a clean database and run `python run.py`.
2. Register the teammate account the participants will assign work to:
   name `Test Teammate`, email `teammate@test.local`, role Team Member.
3. Open a private/incognito window on the home page for each participant.
4. Have a phone or stopwatch ready. Do not demo the app beforehand.

## Task card (give this to the participant)
> You have just joined your company as a **project manager** and you have never
> used this tool before.
>
> 1. Create an account for yourself (use any name and an email like
>    `user1@test.local`) and log in.
> 2. Create a project called **Website Launch**.
> 3. Add a task called **Prepare report** to it.
> 4. Give that task to your colleague **Test Teammate**
>    (`teammate@test.local`).
>
> Tell me when you think you are done.

## Facilitator rules
- Say nothing about how the app works. Encourage thinking aloud.
- Note every point where the participant hesitates, goes to the wrong page or
  makes an error, with the time.
- After the task, ask: "What was the most confusing part?" and write the
  answer down word for word.

## Results (fill in during the test)

| # | Date | Time taken (mm:ss) | Finished <= 10 min | No help given | Result correct | Success | Where they got stuck |
|---|------|--------------------|--------------------|---------------|----------------|---------|----------------------|
| 1 | [FILL IN] | [FILL IN] | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |

**Successes:** [FILL IN] of 5 &nbsp;&nbsp; **Average time:** [FILL IN]
&nbsp;&nbsp; **Result:** [PASS if 5 of 5 / FAIL]

If any participant fails, write down why, fix the cause, and test a **new**
participant. Do not re-test the same person, because they have now learned the
screens.

## Design changes made for this requirement
Found by walking through the first-time flow before testing:

| Problem for a first-time user | Change |
|-------------------------------|--------|
| After creating a project the page gave no hint about what to do next. | The success message now says to add the first task, and an empty project shows a **Next step** box linking to the Add a task form. |
| Not obvious that only the Project Manager role can create projects and assign tasks. | The sign-up form explains it next to the role choice and the role label says "Create projects & assign tasks". |
| Unclear who can be assigned (only project members). | Help text under the Assignee list says so, and tells a lone creator to add teammates by email in the Members panel. |

Automated check: `tests/test_bl31_usability.py` runs the whole journey (register,
log in, create a project, add a task assigned to yourself, find it in My Tasks)
in 6 requests and fails if the next-step guidance disappears. It protects the
design changes; it does not replace the 5-person test above.
