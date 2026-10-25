# Test Cases - Mini Project Management Software (Team 14)

Prepared by: Sakshi P Shetty (tester, Sprint 1)
Covers: BL-44 (auth and security), BL-45 (projects, tasks, allocation), BL-46 (status, dashboard, overdue)
Source: SRS v1.0 acceptance criteria (AC-F-xxx, PRJ-SR-xxx). Test case IDs match the SRS RTM.

Status codes: **Pass**, **Fail** (bug raised as a GitHub issue), **Not run** (feature not merged yet).

---

## 1. Authentication and security (BL-44)

| TC ID | Req | Steps | Test data | Expected result | Status |
|---|---|---|---|---|---|
| TC-Auth-01a | MPMS-F-001 | Open /register, fill all fields, submit | Asha / a@b.com / Passw0rdX | "Account created" shown, redirected to login | Pass (PR #54) |
| TC-Auth-01b | MPMS-F-001 | Register again with the same email | a@b.com | "already exists" error, no second account | Pass (PR #54) |
| TC-Auth-01c | MPMS-F-001 | Register with an invalid email | notanemail | "Enter a valid email address" | Pass (PR #54) |
| TC-Auth-01d | MPMS-F-001 | Register with a blank name | (spaces) | "Name is required" | Pass (PR #54) |
| TC-Auth-02a | MPMS-F-002 | Log in with correct email and password | a@b.com / Passw0rdX | Logged in, name and role shown in navbar | Pass (PR #54) |
| TC-Auth-02b | MPMS-F-002 | Log in with wrong password | Wrong1234 | Generic "Invalid email or password." | Pass (PR #54) |
| TC-Auth-02c | MPMS-F-002 | Log in with an email that does not exist | nobody@b.com | Same generic message (does not reveal which field is wrong) | Pass (PR #54) |
| TC-Auth-02d | MPMS-F-002 | Log in with the email in capitals | A@B.COM | Login succeeds (email is case-insensitive) | Pass (PR #54) |
| TC-Auth-03a | MPMS-F-003 | Enter a wrong password 5 times, then try a 6th time | Wrong1234 x6 | 6th attempt shows "Account locked", lock lasts 15 min | Pass (PR #54) |
| TC-Auth-03b | MPMS-F-003 | After the 5 failures, try the correct password | Passw0rdX | Still blocked during the 15-minute window | Pass (PR #54) |
| TC-Auth-03c | MPMS-F-003 | Wait until the lock window ends, log in correctly | Passw0rdX | Login succeeds, counter reset | Pass (PR #54) |
| TC-Auth-03d | MPMS-F-003 / PRJ-SR-006 | Check activity_logs after the lockout | - | "failed login" entries and "account locked after failed logins" recorded | Pass (PR #54) |
| TC-Auth-04a | MPMS-F-004 | Log in as Team Member, open create-project page | Team Member account | Access denied with a message | Not run |
| TC-Auth-04b | MPMS-F-004 | Log in as Team Member, try to assign a task | Team Member account | Access denied with a message | Not run |
| TC-Auth-04c | MPMS-F-004 | Log in as PM, create a project | PM account | Allowed | Not run |
| TC-Auth-05a | MPMS-F-005 | Log in, click Log out, then open a protected page | - | Redirected to login | Not run |
| TC-Auth-05b | MPMS-F-005 | Log in, stay idle 30 min, click any link | - | Session expired, redirected to login | Not run |
| TC-Sec-01 | PRJ-SR-001 | Open the site with http:// | - | Redirected to https:// | Not run |
| TC-Sec-02 | PRJ-SR-002 | Register, then inspect users.password_hash in the DB | Passw0rdX | Only a salted hash (e.g. scrypt:...), no plain password | Pass (PR #54) |
| TC-Sec-03 | PRJ-SR-003 | As a user of project A, open project B's URL directly | /projects/<B id> | 403 Forbidden | Not run |
| TC-Sec-04a | PRJ-SR-004 | Register with name `<script>alert(1)</script>`, log in | - | Name shown as text, no script runs | Pass (PR #54) |
| TC-Sec-04b | PRJ-SR-004 | Enter `' OR '1'='1` as email at login | - | Login fails normally, no error page | Not run |
| TC-Sec-05 | PRJ-SR-005 | Copy session cookie, log out, reuse the cookie | - | Request rejected, redirected to login | Not run |
| TC-Sec-06 | PRJ-SR-006 | Do a failed login, a role change and a deletion | - | One log entry per event with user and time | Not run |
| TC-Sec-07a | PRJ-SR-007 | Register with a 5-character password | short | "at least 8 characters" | Pass (PR #54) |
| TC-Sec-07b | PRJ-SR-007 | Register with letters only | abcdefgh | "must contain a digit" | Pass (PR #54) |
| TC-Sec-07c | PRJ-SR-007 | Register with digits only | 12345678 | "must contain a letter" | Pass (PR #54) |

---

## 2. Projects, tasks and allocation (BL-45)

| TC ID | Req | Steps | Test data | Expected result | Status |
|---|---|---|---|---|---|
| TC-Prj-01a | MPMS-F-010 | As PM, create a project with name, description, dates | Demo / 20-10 to 30-10 | Project saved and shown in project list | Not run |
| TC-Prj-01b | MPMS-F-010 | Create a project with end date before start date | 30-10 to 20-10 | Error, project not saved | Not run |
| TC-Prj-01c | MPMS-F-010 | Create a project with a blank name | - | Error "name required" | Not run |
| TC-Prj-02 | MPMS-F-011 | Edit project name, save, reload page | New name | New name persists after reload | Not run |
| TC-Prj-03 | MPMS-F-012 | Archive a project | - | Hidden from active list, visible under archived | Not run |
| TC-Prj-04a | MPMS-F-013 | Add a registered user as a member | member@b.com | Member sees the project after logging in | Not run |
| TC-Prj-04b | MPMS-F-013 | Remove that member | - | Member no longer sees the project | Not run |
| TC-Prj-05 | MPMS-F-014 | Log in as a user who is in no projects | - | Project list is empty; other projects not visible | Not run |
| TC-Tsk-01a | MPMS-F-020 | As PM, create a task with title, description, priority, due date | Fix login / High / 25-10 | Task appears in list with status "To Do" | Not run |
| TC-Tsk-01b | MPMS-F-020 | Create a task with a blank title | - | Error, task not saved | Not run |
| TC-Tsk-02 | MPMS-F-021 | Edit a task's priority | Low -> High | Change saved and recorded in activity log | Not run |
| TC-Tsk-03a | MPMS-F-022 | Click delete on a task, then Cancel | - | Task still exists | Not run |
| TC-Tsk-03b | MPMS-F-022 | Click delete on a task, then Confirm | - | Task removed | Not run |
| TC-Tsk-04 | MPMS-F-023 | Add a comment to a task | "Started" | Comment shows author name and timestamp | Not run |
| TC-All-01a | MPMS-F-030 | Open the assign dropdown on a task | - | Only members of that project are listed | Not run |
| TC-All-01b | MPMS-F-030 | Assign the task to a member | member@b.com | Assignee name shown on the task | Not run |
| TC-All-02 | MPMS-F-031 | Reassign the task to another member | - | Old assignee no longer sees it in My Tasks; change logged | Not run |
| TC-All-03 | MPMS-F-032 | Log in as member with 3 tasks (due 30-10, 22-10, 26-10), open My Tasks | - | Only own tasks, ordered 22-10, 26-10, 30-10 | Not run |

---

## 3. Status updates, dashboard and overdue (BL-46)

| TC ID | Req | Steps | Test data | Expected result | Status |
|---|---|---|---|---|---|
| TC-Prg-01a | MPMS-F-040 | As assignee, change status To Do -> In Progress | - | Saved immediately, shown on the task | Not run |
| TC-Prg-01b | MPMS-F-040 | Check every status value | To Do / In Progress / In Review / Done | All four can be selected and saved | Not run |
| TC-Prg-01c | MPMS-F-040 | As a member who is not the assignee, try to change status | - | Not allowed | Not run |
| TC-Prg-02a | MPMS-F-041 | Project with 10 tasks, mark 4 as Done, open dashboard | - | Shows 40% complete | Not run |
| TC-Prg-02b | MPMS-F-041 | Same project, check counts per status | 4 Done, rest mixed | Counts per status add up to 10 | Not run |
| TC-Prg-02c | MPMS-F-041 | Project with 0 tasks, open dashboard | - | Shows 0% (no crash / divide-by-zero) | Not run |
| TC-Prg-03a | MPMS-F-042 | Task due yesterday, status In Progress | due = yesterday | Flagged as overdue on list and dashboard | Not run |
| TC-Prg-03b | MPMS-F-042 | Task due yesterday, status Done | due = yesterday | Not flagged | Not run |
| TC-Prg-03c | MPMS-F-042 | Task due today, status To Do | due = today | Not flagged (only past dates are overdue) | Not run |

---

## 4. Smoke test on main before the demo video (BL-49)

Run on the latest `main`, fresh database (`python init_db.py --reset`, then `python run.py`).

| Step | Action | Expected | Result |
|---|---|---|---|
| 1 | Register a PM account and log in | Logged in as PM | |
| 2 | Create a project | Project listed | |
| 3 | Register a member account; add it to the project | Member added | |
| 4 | Create a task and assign it to the member | Assignee shown | |
| 5 | Log in as the member, open My Tasks | Task listed | |
| 6 | Change its status to Done | Status saved | |
| 7 | Log in as PM, open dashboard | % complete updated | |
