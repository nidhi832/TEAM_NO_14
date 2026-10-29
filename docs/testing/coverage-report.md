# Test coverage report - BL-34 (MPMS-NF-006)

**Result: PASS** - 97.7% of the application code is covered by tests (target: at least 60%).

Generated: 29 Oct 2026 20:22 | Commit: `6a98a51` | Tests passed: 120

## How to reproduce

    pip install -r requirements.txt
    python scripts/coverage_report.py

The same check runs in CI on every pull request (`pytest --cov=app`, configured in `.coveragerc`) and fails below the target.

## Coverage per file

| File | Statements | Missed | Covered |
|---|---|---|---|
| app/__init__.py | 22 | 0 | 100% |
| app/auth_utils.py | 48 | 0 | 100% |
| app/db_tuning.py | 12 | 1 | 92% |
| app/extensions.py | 2 | 0 | 100% |
| app/models.py | 58 | 0 | 100% |
| app/models_session.py | 9 | 0 | 100% |
| app/routes/__init__.py | 9 | 0 | 100% |
| app/routes/admin.py | 32 | 0 | 100% |
| app/routes/auth.py | 69 | 1 | 99% |
| app/routes/dashboard.py | 10 | 0 | 100% |
| app/routes/projects.py | 128 | 7 | 95% |
| app/routes/reports.py | 21 | 0 | 100% |
| app/routes/tasks.py | 145 | 4 | 97% |
| app/security.py | 22 | 1 | 95% |
| app/services/__init__.py | 0 | 0 | 100% |
| app/services/admin_service.py | 36 | 0 | 100% |
| app/services/audit_service.py | 16 | 0 | 100% |
| app/services/auth_service.py | 58 | 0 | 100% |
| app/services/project_service.py | 35 | 0 | 100% |
| app/services/report_service.py | 64 | 1 | 98% |
| app/services/session_service.py | 40 | 3 | 92% |
| app/services/task_service.py | 38 | 1 | 97% |
| app/session_security.py | 32 | 2 | 94% |
| **Total** | **906** | **21** | **97.7%** |

Statement coverage only (a line counts as covered when a test runs it). The layering rules are checked separately by `tests/test_architecture.py`; the manual review is in `docs/code-review.md`.
