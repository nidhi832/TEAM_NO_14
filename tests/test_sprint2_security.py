"""Tests for BL-09 (logout / idle timeout), BL-39 (session tokens),
BL-27 (admin user accounts), BL-28 (activity log), BL-40 (security events)."""
from datetime import timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import ActivityLog, User
from app.models_session import UserSession
from app.services import auth_service

PASSWORD = "Passw0rdX"


@pytest.fixture()
def app():
    app = create_app({"TESTING": True,
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(email, role="Team Member", active=True):
    user = User(name=email.split("@")[0].title(), email=email, role=role,
                is_active=active,
                password_hash=auth_service.hash_password(PASSWORD))
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email, password=PASSWORD):
    resp = client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True)
    client.get("/")          # first request after login creates the token
    return resp


def actions():
    return [a.action for a in ActivityLog.query.all()]


# ---------- BL-09 / BL-39: sessions ----------

def test_login_creates_server_side_token(client):
    make_user("m@b.com")
    login(client, "m@b.com")
    with client.session_transaction() as sess:
        token = sess.get("sid")
    assert token and len(token) >= 32
    assert UserSession.query.filter_by(token=token, revoked=False).count() == 1


def test_logout_revokes_token_and_old_cookie_is_rejected(client):
    make_user("m@b.com")
    login(client, "m@b.com")
    with client.session_transaction() as sess:
        stolen = dict(sess)                       # copy of the cookie
    client.get("/logout")
    with client.session_transaction() as sess:    # attacker replays it
        sess.update(stolen)
    resp = client.get("/tasks/search", follow_redirects=True)
    assert b"no longer valid" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess
    assert "logged out" in actions()


def test_idle_30_minutes_logs_out(client):
    make_user("m@b.com")
    login(client, "m@b.com")
    record = UserSession.query.one()
    record.last_seen -= timedelta(minutes=31)
    db.session.commit()
    resp = client.get("/tasks/search", follow_redirects=True)
    assert b"expired after 30 minutes" in resp.data
    assert b"Log in" in resp.data
    assert "session expired after inactivity" in actions()


def test_activity_within_30_minutes_keeps_session(client):
    make_user("m@b.com")
    login(client, "m@b.com")
    record = UserSession.query.one()
    record.last_seen -= timedelta(minutes=29)
    db.session.commit()
    assert client.get("/tasks/search").status_code == 200


def test_deactivated_user_is_kicked_out_immediately(client):
    user = make_user("m@b.com")
    login(client, "m@b.com")
    user.is_active = False
    db.session.commit()
    resp = client.get("/tasks/search")
    assert resp.status_code == 302 and "/login" in resp.location
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_protected_page_needs_login(client):
    resp = client.get("/tasks/search")
    assert resp.status_code == 302 and "/login" in resp.location


# ---------- BL-27: admin user accounts ----------

def test_team_member_cannot_open_admin_pages(client):
    make_user("m@b.com")
    login(client, "m@b.com")
    assert client.get("/admin/users").status_code == 403
    assert client.get("/admin/log").status_code == 403


def test_admin_deactivates_and_reactivates(client):
    make_user("admin@b.com", role="Admin")
    member = make_user("m@b.com")
    login(client, "admin@b.com")
    assert b"m@b.com" in client.get("/admin/users").data

    client.post(f"/admin/users/{member.id}/deactivate")
    assert db.session.get(User, member.id).is_active is False
    client.get("/logout")
    resp = login(client, "m@b.com")
    assert b"deactivated" in resp.data            # AC-F-050

    login(client, "admin@b.com")
    client.post(f"/admin/users/{member.id}/reactivate")
    assert db.session.get(User, member.id).is_active is True


def test_admin_cannot_deactivate_self(client):
    admin = make_user("admin@b.com", role="Admin")
    login(client, "admin@b.com")
    resp = client.post(f"/admin/users/{admin.id}/deactivate",
                       follow_redirects=True)
    assert b"cannot change your own" in resp.data
    assert db.session.get(User, admin.id).is_active is True


def test_admin_changes_role_and_bad_role_rejected(client):
    make_user("admin@b.com", role="Admin")
    member = make_user("m@b.com")
    login(client, "admin@b.com")
    client.post(f"/admin/users/{member.id}/role", data={"role": "PM"})
    assert db.session.get(User, member.id).role == "PM"
    resp = client.post(f"/admin/users/{member.id}/role",
                       data={"role": "SuperUser"}, follow_redirects=True)
    assert b"Unknown role" in resp.data
    assert db.session.get(User, member.id).role == "PM"


# ---------- BL-28 / BL-40: activity log and security events ----------

def test_security_events_are_logged_and_shown(client):
    make_user("admin@b.com", role="Admin")
    member = make_user("m@b.com")
    login(client, "m@b.com", password="Wrong1234")     # failed login (BL-06)
    login(client, "admin@b.com")
    client.post(f"/admin/users/{member.id}/role", data={"role": "PM"})
    client.post(f"/admin/users/{member.id}/deactivate")

    logged = actions()
    assert "failed login" in logged
    assert any(a.startswith("role changed: m@b.com Team Member -> PM")
               for a in logged)
    assert any(a.startswith("account deactivated") for a in logged)

    page = client.get("/admin/log?security=1").data
    assert b"failed login" in page and b"role changed" in page
    assert b"Admin" in page                          # who did it


# ---------- BL-29: SQLite tuned for concurrent users ----------

def test_sqlite_busy_timeout_and_wal(app, tmp_path):
    from sqlalchemy import create_engine, text
    import app.db_tuning  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 15000
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
