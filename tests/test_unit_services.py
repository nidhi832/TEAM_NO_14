"""BL-34: unit tests for the business layer (rules, not pages)."""
import pytest

from app.extensions import db
from app.models import User
from app.services import admin_service, project_service


# ---- project_service: pure functions, no database -----------------------------
def test_parse_date():
    assert str(project_service.parse_date("2026-10-30")) == "2026-10-30"
    assert project_service.parse_date("  ") is None
    assert project_service.parse_date(None) is None
    with pytest.raises(ValueError):
        project_service.parse_date("30/10/2026")


def test_validate_project_ok_returns_dates():
    problems, start, end = project_service.validate_project(
        "Alpha", "2026-10-01", "2026-10-30")
    assert problems == []
    assert str(start) == "2026-10-01" and str(end) == "2026-10-30"


@pytest.mark.parametrize("name, start, end, expected", [
    ("", "", "", "name is required"),
    ("x" * 121, "", "", "120 characters"),
    ("Alpha", "tomorrow", "", "YYYY-MM-DD"),
    ("Alpha", "2026-10-30", "2026-10-01", "before the start"),
])
def test_validate_project_problems(name, start, end, expected):
    problems, _, _ = project_service.validate_project(name, start, end)
    assert any(expected in p for p in problems)


def test_validate_task_ok_and_problems():
    problems, due = project_service.validate_task("Write", "High", "2026-11-01")
    assert problems == [] and str(due) == "2026-11-01"
    problems, _ = project_service.validate_task("", "Urgent", "soon")
    assert len(problems) == 3
    problems, _ = project_service.validate_task("x" * 151, "Low", "")
    assert any("150 characters" in p for p in problems)


# ---- admin_service: account rules ---------------------------------------------
def make_user(name, role="Team Member", active=True):
    user = User(name=name, email=f"{name.lower()}@unit.test", role=role,
                password_hash="x", is_active=active)
    db.session.add(user)
    db.session.commit()
    return user


def test_set_active_rules(app):
    with app.app_context():
        admin, tom = make_user("Ann", "Admin"), make_user("Tom")
        assert admin_service.set_active(admin, 9999, False) == "User not found."
        assert "own account" in admin_service.set_active(admin, admin.id, False)
        assert admin_service.set_active(admin, tom.id, True) is None  # no-op
        assert admin_service.set_active(admin, tom.id, False) is None
        assert tom.is_active is False


def test_reactivating_clears_the_lockout(app):
    with app.app_context():
        admin = make_user("Ann", "Admin")
        tom = make_user("Tom", active=False)
        tom.failed_attempts = 5
        db.session.commit()
        assert admin_service.set_active(admin, tom.id, True) is None
        assert tom.is_active is True
        assert tom.failed_attempts == 0 and tom.locked_until is None


def test_set_role_rules(app):
    with app.app_context():
        admin, tom = make_user("Ann", "Admin"), make_user("Tom")
        assert admin_service.set_role(admin, tom.id, "King") == "Unknown role."
        assert admin_service.set_role(admin, 9999, "PM") == "User not found."
        assert "own role" in admin_service.set_role(admin, admin.id, "PM")
        assert admin_service.set_role(admin, tom.id, "Team Member") is None
        assert admin_service.set_role(admin, tom.id, "PM") is None
        assert tom.role == "PM"
