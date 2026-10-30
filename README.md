<div align="center">

# 📋 Mini Project Management Software

**Plan • Organize • Track — all in one place**

*Developed by Team No. 14*

</div>

---

## 📖 About the Project

**Mini Project Management Software** is a simple tool that helps teams plan, organize, and track their project work in one place. It replaces scattered notes, chats, and spreadsheets with a single system where everyone can see **what needs to be done, who is doing it, and how far the project has progressed.**

---

## ❗ Problem Statement

Small teams often struggle to keep track of tasks, deadlines, and responsibilities. Work gets delayed or duplicated because there is no clear, shared view of the project.

> 💡 **Our solution:** an easy-to-use system that gives teams full visibility without the complexity of large enterprise tools.

---

## 🎯 Objectives

- ✅ Make it easy to create and manage projects
- ✅ Let teams assign tasks and set deadlines
- ✅ Track task status: *To Do → In Progress → In Review → Done*
- ✅ Give a clear overview of overall project progress
- ✅ Keep the system simple, fast, secure, and easy to learn

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📁 **Project Management** | Create, edit, archive and restore projects; add or remove members |
| 📝 **Task Management** | Add, edit and delete tasks (with confirmation); set priority and due date; comment on tasks |
| 👤 **Task Allocation** | Assign and reassign tasks to project members; "My Tasks" list sorted by due date |
| 📊 **Progress Tracking** | Update task status; dashboard with % complete, counts per status, and red **Overdue** badges |
| 🔍 **Search & Reports** | Search tasks by title, filter by status, priority, assignee, due date and project; download a CSV progress report |
| 🛡️ **Admin** | Deactivate / reactivate users, change roles, view the activity log with a "Security events only" filter |
| 🔐 **Security** | Roles (Admin, Project Manager, Team Member), hashed passwords, lockout after 5 failed logins, 30-minute idle logout, permission checks on every page |

---

## 👥 Who Is It For?

| User | Benefit |
|---|---|
| 🎓 **Student & small teams** | A simple way to organize group projects |
| 🧑‍💼 **Team leaders (Project Managers)** | Monitor progress and deadlines easily |
| 👨‍💻 **Team members** | Clear view of their own tasks and responsibilities |
| 🛡️ **Admins** | Manage user accounts and review an audit trail |

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python init_db.py                          # create the database
python run.py                              # open http://127.0.0.1:5000
python create_admin.py you@example.com     # make the first Admin (register first)
python -m pytest                           # run all automated tests
```

Register as a **Project Manager** to create projects, or as a **Team Member** to work on tasks.

---

## 🛠️ Tech Stack

Python 3.11+ · Flask 3 · Flask-SQLAlchemy · SQLite · Bootstrap 5 · pytest + pytest-cov · flake8 · GitHub Actions CI

---

## ✅ Quality

| Check | Result |
|---|---|
| Automated tests | 141 tests, run on every pull request (GitHub Actions) |
| Code coverage | 97.7% (target 60%) |
| Response time, 50 concurrent users | 95% of requests in 0.30 s (target 2 s) |
| Availability | 100% over 180 health checks (target 99%) |
| Backup & restore | Verified |

---

## 📚 Documents & Demos

| Item | Link |
|---|---|
| Software Requirements Specification (v2.0) | [SRS_Mini_Project_Management_Software.docx](SRS_Mini_Project_Management_Software.docx) |
| Software Architecture & Design (v2.0) | [SAD_Mini_Project_Management_Software.docx](SAD_Mini_Project_Management_Software.docx) |
| Test cases | [docs/testing/test-cases.md](docs/testing/test-cases.md) |
| Test reports | [Performance](docs/testing/performance-report.md) · [Availability](docs/testing/uptime-report.md) · [Coverage](docs/testing/coverage-report.md) · [Backup](docs/testing/database-backup.md) · [Usability](docs/testing/usability-test.md) |
| Sprint 1 demo (1 min) | [docs/sprint1-demo.mp4](docs/sprint1-demo.mp4) |
| Sprint 2 demo (2 min) | [docs/sprint2-demo.mp4](docs/sprint2-demo.mp4) |

---

## 👩‍💻 Team

| Member | SRN | Role |
|---|---|---|
| Srinidhi P | PES1UG24AM407 | Repository & process owner; Sprint 2 reviewer |
| Sanjana V Shastry | PES1UG24AM916 | Backlog creator; Sprint 2 programmer |
| Sakshi P Shetty | PES1UG24AM395 | Estimation & sprint planner; Sprint 1 tester; Sprint 2 programmer |

---

## 🗓️ Sprint Plan

| Sprint | Dates |
|---|---|
| Sprint 0 (backlog setup, dry run) | 12 - 16 Oct 2026 |
| Sprint 1 | 19 - 23 Oct 2026 |
| Sprint 2 | 26 - 30 Oct 2026 |

Work is tracked as GitHub issues `[BL-01]` to `[BL-49]` on the project board; every change goes through a pull request checked by CI.
