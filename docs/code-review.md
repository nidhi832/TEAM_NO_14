# Code review - BL-34 (MPMS-NF-006 Maintainability)

**Requirement:** the code is layered and has unit tests covering at least 60%
of it. **Result: PASS** - layering holds with the small exceptions below, and
tests cover 97.7% of the application code.

Reviewer: Sanjana V Shastry | Date: 29 Oct 2026 | Reviewed: `main` at
`6a98a51` (read every module under `app/`, ran flake8, pytest and coverage)

## Layers
| Layer | Where | Job |
|---|---|---|
| Data | `app/models.py`, `app/models_session.py` | tables and relationships only |
| Business | `app/services/*.py` | rules: validation, lockout, % complete, search, reports, audit log |
| UI | `app/routes/*.py` + `app/templates/` | read the request, call a service, return a page |
| Cross-cutting | `app/auth_utils.py`, `app/security.py`, `app/session_security.py` | login, roles, project access, HTTPS, session checks |

Dependencies point one way: routes -> services -> models. This is enforced by
`tests/test_architecture.py`, which fails if
- the data layer imports services, routes or Flask,
- a service imports routes or Flask,
- `auth_service.py` imports Flask, SQLAlchemy or any `app` module (it is
  documented as pure),
- a route contains raw SQL.

## Checklist
| Check | Result |
|---|---|
| Layers separated, one direction of dependency | Pass (tested) |
| No raw SQL in routes; queries go through SQLAlchemy (parameterised) | Pass (tested) |
| Business rules testable without a web request | Pass - `auth_service`, `project_service`, `task_service`, `uptime_service` are plain functions |
| Unit tests for the business layer | Pass - `test_auth_service.py`, `test_unit_services.py`, others |
| Test coverage >= 60% | 97.7% (`docs/testing/coverage-report.md`) |
| Coverage enforced automatically | Pass - CI runs `pytest --cov=app` and fails under 60% (`.coveragerc`) |
| Every module has a docstring naming the backlog item | Pass, except `app/extensions.py` (3 lines) |
| Functions short and single-purpose | Pass - longest is `create_task` (44 lines); the rest are under 40 |
| Style | Partly - CI only checks syntax and undefined names; full flake8 reports 24 style notes in `app/` (17 long lines, 7 whitespace/indent) |

## Findings (not changed in this review)
1. **Routes save data themselves.** `auth.py`, `projects.py` and `tasks.py`
   create and change model objects and call `db.session.commit()` (11
   places). Validation and rules are in services, but the saving is not.
   *Suggestion:* move the writes into services, one function per action.
2. **Two logging helpers.** `auth_utils.log_event(action, ...)` uses the
   logged-in user; `audit_service.log_event(user_id, action, ...)` takes the
   user as a parameter. *Suggestion:* keep one.
3. **`report_service` imports `auth_utils`** (for `visible_projects` and
   `can_manage_project`), and `auth_utils` imports Flask. The business layer
   therefore depends on a Flask-aware module indirectly.
   *Suggestion:* move the two project-access functions into a service.
4. **Deprecated `datetime.utcnow()`** is used 5 times (Python 3.12 prints a
   warning in the tests). *Suggestion:* `datetime.now(timezone.utc)`.
5. **Hard-coded `SECRET_KEY="dev-change-me"`** in `app/__init__.py`. Fine for
   development; production must set its own secret from an environment
   variable.
6. **No CSRF tokens** on the POST forms. Logging in is protected by session
   cookies only. *Suggestion:* add Flask-WTF `CSRFProtect` before any real
   deployment.

None of these stops the requirement from being met; items 5 and 6 matter
before real use.

## Fixed in this change
- Removed two empty files named `git` and `python` that had been committed to
  the repository root by mistake.
- Added the architecture tests, unit tests for `project_service` and
  `admin_service`, the coverage gate in CI, and `scripts/coverage_report.py`.
