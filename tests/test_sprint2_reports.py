"""Tests for BL-25 (filter / search tasks) and BL-26 (CSV progress report)."""
import csv
import io
from datetime import date, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import Project, Task, User
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


def make_user(email, role="Team Member"):
    user = User(name=email.split("@")[0].title(), email=email, role=role,
                password_hash=auth_service.hash_password(PASSWORD))
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email):
    client.post("/login", data={"email": email, "password": PASSWORD})
    client.get("/")


@pytest.fixture()
def data(app):
    pm = make_user("pm@b.com", role="PM")
    asha = make_user("asha@b.com")
    ravi = make_user("ravi@b.com")
    outsider = make_user("out@b.com")
    today = date.today()
    alpha = Project(name="Alpha", owner_id=pm.id, members=[pm, asha, ravi])
    beta = Project(name="Beta", owner_id=outsider.id, members=[outsider])
    db.session.add_all([alpha, beta])
    db.session.flush()
    db.session.add_all([
        Task(project_id=alpha.id, title="Signin form", priority="High",
             status="Done", assignee_id=asha.id,
             due_date=today - timedelta(days=2)),
        Task(project_id=alpha.id, title="Charts widget", priority="High",
             status="In Progress", assignee_id=ravi.id,
             due_date=today - timedelta(days=1)),
        Task(project_id=alpha.id, title="=HYPERLINK(evil)", priority="Low",
             status="To Do", assignee_id=asha.id,
             due_date=today + timedelta(days=5)),
        Task(project_id=beta.id, title="Secret beta task", priority="High",
             status="To Do", assignee_id=outsider.id),
    ])
    db.session.commit()
    return {"pm": pm, "asha": asha, "ravi": ravi, "alpha": alpha,
            "beta": beta, "today": today}


def titles(resp):
    return [t for t in ("Signin form", "Charts widget", "=HYPERLINK(evil)",
                        "Secret beta task") if t.encode() in resp.data]


# ---------- BL-25: filter and search ----------

def test_search_by_title_and_only_own_projects(client, data):
    login(client, "asha@b.com")
    resp = client.get("/tasks/search?q=signin")
    assert titles(resp) == ["Signin form"]
    resp = client.get("/tasks/search?q=secret")
    assert titles(resp) == []                   # Beta is not her project


def test_filter_by_status_priority_assignee(client, data):
    login(client, "pm@b.com")
    assert titles(client.get("/tasks/search?status=Done")) == ["Signin form"]
    assert titles(client.get("/tasks/search?priority=Low")) == \
        ["=HYPERLINK(evil)"]
    resp = client.get(f"/tasks/search?assignee_id={data['ravi'].id}")
    assert titles(resp) == ["Charts widget"]


def test_filter_by_due_date_and_overdue_flag(client, data):
    login(client, "pm@b.com")
    resp = client.get(f"/tasks/search?due_before={data['today'].isoformat()}")
    assert titles(resp) == ["Signin form", "Charts widget"]
    assert resp.data.count(b">Overdue<") == 1   # Done task is not overdue


def test_bad_filter_values_are_safe(client, data):
    login(client, "pm@b.com")
    resp = client.get("/tasks/search?due_before=notadate&status=Hacked")
    assert resp.status_code == 200
    assert b"valid date" in resp.data
    resp = client.get("/tasks/search?q=%27%20OR%20%271%27%3D%271")
    assert titles(resp) == []                   # SQL injection text finds nothing


# ---------- BL-26: CSV report ----------

def test_pm_downloads_csv_report(client, data):
    login(client, "pm@b.com")
    resp = client.get(f"/projects/{data['alpha'].id}/report.csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment" in resp.headers["Content-Disposition"]
    rows = list(csv.reader(io.StringIO(resp.get_data(as_text=True))))
    assert rows[0] == ["Task ID", "Title", "Assignee", "Status", "Priority",
                       "Due date", "Overdue"]
    body = rows[1:4]
    assert [r[1] for r in body] == ["Signin form", "Charts widget",
                                    "'=HYPERLINK(evil)"]
    assert body[1][2] == "Ravi" and body[1][6] == "Yes"
    assert rows[-1] == ["Summary", "1 of 3 tasks Done", "33%"]


def test_member_and_outsider_cannot_download(client, data):
    login(client, "asha@b.com")
    assert client.get(f"/projects/{data['alpha'].id}/report.csv"
                      ).status_code == 403
    assert client.get("/projects/999/report.csv").status_code == 404
    login(client, "ravi@b.com")
    assert client.get(f"/projects/{data['beta'].id}/report.csv"
                      ).status_code == 403          # not even a member


def test_navbar_links(client, data):
    login(client, "pm@b.com")
    page = client.get("/tasks/search").data
    assert b"Find tasks" in page and b">Admin<" not in page
