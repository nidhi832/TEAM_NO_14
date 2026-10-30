# Deviations from the submitted SRS, SAD and Test Plan - BL-43

Team 14 - Mini Project Management Software | Updated: 30 Oct 2026

The brief asks that deviations from the submitted documents are documented and
explained at the final demo. This file lists every known deviation, why it
happened and where it is recorded. The updated documents are **SRS v2.0** and
**SAD v2.0** (both describe the system as built).

## 1. Requirements (SRS)

| # | Planned (SRS v1.0) | What we built | Why |
|---|---|---|---|
| R1 | Role not specified at registration | User chooses **Project Manager** or **Team Member** when registering; the first **Admin** is created with `create_admin.py` (new requirement **MPMS-F-006**) | Otherwise nobody could create projects; Admin must not be self-assignable (security) |
| R2 | Admin can view / deactivate / reactivate users | Admin can also **change a user's role**; admins cannot change their own role or status (new requirement **MPMS-F-052**) | Needed to promote users to PM after registration; role changes are logged as security events |
| R3 | Archive hides a project | Archived projects have their own list and can be **restored** | Archiving by mistake should be reversible |
| R4 | Search by status, assignee, priority, due date, title | Also filter by **project**; only the user's own projects are searched | Keeps search consistent with MPMS-F-014 (no access to other projects) |
| R5 | Session ends on logout / 30 min idle | Implemented with an extra **server-side session token** table, so a copied cookie stops working after logout | A signed cookie alone stays valid after logout (PRJ-SR-005) |
| R6 | "Team of four students" (SRS 2.5) | Team of **three** | Corrected in SRS v2.0 |

## 2. Architecture and design (SAD)

| # | Planned | What we built | Why |
|---|---|---|---|
| D1 | Technology "chosen at design time" | **Python 3.11 + Flask 3 + Flask-SQLAlchemy + SQLite + Jinja2/Bootstrap 5**, pytest + GitHub Actions CI | One language for app, tests and CI; runs with one command |
| D2 | Relational database | SQLite with **busy timeout (15 s) + WAL mode** (`app/db_tuning.py`) | The BL-29 load test found `database is locked` (HTTP 500) with 50 users; fixed - 0 errors after |
| D3 | Session "last seen" | Written **at most once a minute** | Reduced database writes under load (BL-29); idle timeout still accurate to 1 minute |
| D4 | No monitoring endpoint | Added **GET /health** + `scripts/uptime_monitor.py` | Needed to measure availability (MPMS-NF-002, BL-30) |
| D5 | - | Frontend **redesigned** in Sprint 2 (BL-32) | Better usability and responsive layout |

## 3. Testing (Test Plan)

| # | Planned | What we did | Why |
|---|---|---|---|
| T1 | Test case IDs like TC-Auth-01 | Each requirement is verified by a named **automated test file** (136 tests, run in CI on every PR); manual cases in `docs/testing/test-cases.md` | Automated tests run on every change |
| T2 | Load test with 50 users | Two modes: **realistic** (1-3 s think time) and **burst** (no pauses) - both PASS (p95 0.30 s / 1.97 s) | Burst is a stricter stress test; see `docs/testing/performance-report.md` |
| T3 | Availability over a test month | Measured for **30 minutes (180 checks, 100%)**, outside working hours | Short project timeline; method and limits in `docs/testing/uptime-report.md` |
| T4 | Usability test with 5 users | Protocol ready; **user test in progress** (BL-31, PR #71) | Done last, after the UI redesign |
| T5 | Browser check on 3 browsers x 3 sizes | Responsive layout built; recorded check **pending** (BL-32) | - |

## 4. Process and work allocation

| # | Planned | What happened | Why |
|---|---|---|---|
| P1 | Sanjana implements BL-10, 13, 15, 19, 21, 23 in Sprint 1 | **Srinidhi implemented them in PR #56** (26 Oct) | To finish Sprint 1 on time |
| P2 | Sprint 2 NFR items owned by Srinidhi | Rebalanced: **Sanjana** took BL-30, 31, 33, 34; **Sakshi** took BL-29, 42; **Srinidhi** did the UI (BL-32) and reviewed / merged PRs | To balance work after P1 |
| P3 | Every change through a PR | Sakshi's Sprint 2 code (BL-09, 25, 26, 27, 28, 39, 40) was **committed directly to main** (commit `e76f247`) by mistake; CI passed and it was tested afterwards. Branch protection was not yet enabled. | Mistake while uploading files through the GitHub website |
| P4 | Sprint 1 ends 23 Oct | Last Sprint 1 items merged on **26 Oct** (PR #56) | Sprint 1 ran late; brief allowed backlog changes |

## 5. Still open at development freeze (30 Oct)

- BL-31 usability test with 5 users (PR #71)
- BL-32 recorded cross-browser check
- Known gaps listed in SAD 4.6: CSRF tokens on forms, `SECRET_KEY` from an environment variable, production WSGI server
