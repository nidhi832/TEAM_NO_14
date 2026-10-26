# Performance test report - BL-29 (MPMS-NF-001)

**Requirement:** common pages and actions (login, project list, task update)
respond within **2 seconds for 95% of requests** with up to **50 concurrent users**.

**Result: PASS** - 95th percentile **0.30 s** (realistic use) and **1.97 s**
(worst-case burst), 0 errors, 900 timed requests.

Tester: Sakshi P Shetty | Date: 26 Oct 2026 | Build: main at 5d50d58 + the BL-29 changes below

## How it was tested
- Script: `scripts/load_test.py` (Python standard library only). Run with
  `python run.py` in one window and `python scripts/load_test.py [--burst]` in another.
- **Setup (not timed):** one PM, one project, 50 Team Members added to it, one task each.
- **Timed actions, all 50 users in parallel, 3 rounds each:** log in, open the
  project list, update the status of their own task (150 requests per action).
- **Realistic mode (default):** users start within the first 5 s and pause 1-3 s
  between clicks ("think time"), like real people.
- **Burst mode (`--burst`):** no pauses at all - every user hits the server at
  the same instant. This is a stress test, harsher than the requirement.
- **Environment:** Sakshi's laptop, Windows 11, Python 3.12.7, Flask development
  server (`python run.py`, debug on), SQLite database. App and test on the same machine.

## Results (after the fixes)

**Realistic mode** - 50 users, 450 requests, 0 errors

| Action | Requests | p50 (s) | p95 (s) | max (s) |
|---|---|---|---|---|
| Login | 150 | 0.253 | 0.323 | 0.363 |
| Project list | 150 | 0.026 | 0.044 | 0.082 |
| Task status update | 150 | 0.057 | 0.100 | 0.145 |
| **All** | **450** | **0.058** | **0.296** | **0.363** |

**Burst mode (worst case)** - 50 users, 450 requests, 0 errors

| Action | Requests | p50 (s) | p95 (s) | max (s) |
|---|---|---|---|---|
| Login | 150 | 1.762 | 2.075 | 2.310 |
| Project list | 150 | 0.533 | 0.809 | 1.034 |
| Task status update | 150 | 0.967 | 1.521 | 2.254 |
| **All** | **450** | **0.933** | **1.967** | **2.310** |

Both modes meet the target (95th percentile <= 2.0 s).

## Problems found and fixed

| # | Problem found by the test | Cause | Fix |
|---|---|---|---|
| 1 | Burst run: 1 request crashed with **HTTP 500** - `sqlite3.OperationalError: database is locked` (in login) | SQLite allows one write at a time and gave up immediately when another user was writing | `app/db_tuning.py`: SQLite **busy timeout 15 s** (wait instead of failing) + **WAL journal mode** (reads don't block writes). Test added. |
| 2 | Every request wrote to the database to update "last seen" for the 30-min idle timeout (BL-09/39) | Extra write per request -> more lock contention | `session_service.py`: update last_seen **at most once a minute** (idle timeout still accurate to 1 min) |

**Before vs after (burst mode, same laptop):**

| | Errors | p95 (s) | Result |
|---|---|---|---|
| Before fixes (20:33) | 14 (1x HTTP 500 database locked, 13x connection reset) | 1.884 (of 408 successful) | FAIL |
| After fixes (20:41) | **0** | **1.967** | **PASS** |

## Observations and limits
- **Login is the slowest action** because password checking uses deliberately slow,
  salted **scrypt** hashing (BL-36 / PRJ-SR-002). This is a security feature, so it
  was **not** weakened to make the test faster.
- The "connection reset" errors seen before the fix came from the Flask
  **development** server under a sudden burst; they disappeared once requests no
  longer waited on the database lock. For real deployment a production WSGI server
  (e.g. waitress or gunicorn) should be used.
- App and load generator ran on the same laptop, so results include CPU shared
  between them; a separate server would be faster, not slower.

## Files
- `scripts/load_test.py` - the load test (new)
- `app/db_tuning.py` - SQLite busy timeout + WAL (new)
- `app/__init__.py` - loads db_tuning (1 line)
- `app/services/session_service.py` - last_seen written at most once a minute
- `tests/test_sprint2_security.py` - new test for the SQLite settings
