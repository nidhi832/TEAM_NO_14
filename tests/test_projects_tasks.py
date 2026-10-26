"""Tests for BL-08, 10, 13, 14, 15, 19, 21, 22, 23, 24, 35."""
from datetime import date, timedelta

from app.extensions import db
from app.models import Project, Task, User
from app.services import auth_service, task_service

PASSWORD = "Passw0rdX"


def make_user(name, role):
    user = User(name=name, email=f"{name.lower()}@x.com", role=role,
                password_hash=auth_service.hash_password(PASSWORD))
    db.session.add(user)
    db.session.commit()
    return user


def login(client, user):
    client.post("/login", data={"email": user.email, "password": PASSWORD})


def make_project(owner, members=(), name="Demo"):
    project = Project(name=name, owner_id=owner.id)
    project.members.append(owner)
    for m in members:
        project.members.append(m)
    db.session.add(project)
    db.session.commit()
    return project


def make_task(project, title="T", assignee=None, due=None, status="To Do"):
    task = Task(project_id=project.id, title=title, due_date=due,
                status=status, assignee_id=assignee.id if assignee else None)
    db.session.add(task)
    db.session.commit()
    return task


# ---- BL-08 roles ----------------------------------------------------------
def test_team_member_cannot_create_project(app, client):
    with app.app_context():
        login(client, make_user("Tom", "Team Member"))
        assert client.get("/projects/new").status_code == 403
        assert client.post("/projects/new", data={"name": "X"}).status_code == 403


def test_pages_require_login(client):
    for url in ("/projects", "/my-tasks", "/dashboard"):
        assert client.get(url).status_code == 302


def test_register_lets_user_pick_pm_but_not_admin(client):
    client.post("/register", data={"name": "P", "email": "p@x.com",
                                   "password": PASSWORD, "role": "PM"})
    client.post("/register", data={"name": "A", "email": "a@x.com",
                                   "password": PASSWORD, "role": "Admin"})
    with client.application.app_context():
        assert User.query.filter_by(email="p@x.com").one().role == "PM"
        assert User.query.filter_by(email="a@x.com").first() is None


# ---- BL-10 create project ---------------------------------------------------
def test_pm_creates_project_and_is_member(app, client):
    with app.app_context():
        pm = make_user("Pam", "PM")
        login(client, pm)
        resp = client.post("/projects/new", data={
            "name": "Alpha", "start_date": "2026-10-01",
            "end_date": "2026-10-30"}, follow_redirects=True)
        assert b"Project created" in resp.data
        project = Project.query.filter_by(name="Alpha").one()
        assert pm in project.members and project.owner_id == pm.id


def test_end_date_before_start_is_rejected(app, client):
    with app.app_context():
        login(client, make_user("Pam", "PM"))
        resp = client.post("/projects/new", data={
            "name": "Bad", "start_date": "2026-10-30",
            "end_date": "2026-10-01"})
        assert resp.status_code == 400
        assert Project.query.count() == 0


# ---- BL-13 members / BL-14 visibility ---------------------------------------
def test_add_and_remove_member(app, client):
    with app.app_context():
        pm, tom = make_user("Pam", "PM"), make_user("Tom", "Team Member")
        project = make_project(pm)
        task = make_task(project, assignee=None)
        login(client, pm)
        client.post(f"/projects/{project.id}/members", data={"email": tom.email})
        assert tom in db.session.get(Project, project.id).members
        task.assignee_id = tom.id
        db.session.commit()
        client.post(f"/projects/{project.id}/members/{tom.id}/remove")
        assert tom not in db.session.get(Project, project.id).members
        assert db.session.get(Task, task.id).assignee_id is None


def test_user_sees_only_own_projects(app, client):
    with app.app_context():
        pm, tom, eve = (make_user("Pam", "PM"), make_user("Tom", "Team Member"),
                        make_user("Eve", "Team Member"))
        mine = make_project(pm, [tom], name="Shared")
        other = make_project(pm, name="Secret")
        login(client, tom)
        page = client.get("/projects").data
        assert b"Shared" in page and b"Secret" not in page
        assert client.get(f"/projects/{mine.id}").status_code == 200
        assert client.get(f"/projects/{other.id}").status_code == 403


# ---- BL-15 / BL-19 tasks and assignment ---------------------------------------
def test_pm_creates_task_with_status_todo(app, client):
    with app.app_context():
        pm, tom = make_user("Pam", "PM"), make_user("Tom", "Team Member")
        project = make_project(pm, [tom])
        login(client, pm)
        client.post(f"/projects/{project.id}/tasks", data={
            "title": "Write docs", "priority": "High", "due_date": "2026-11-01",
            "assignee_id": str(tom.id)})
        task = Task.query.one()
        assert task.status == "To Do" and task.assignee_id == tom.id


def test_cannot_assign_non_member(app, client):
    with app.app_context():
        pm, eve = make_user("Pam", "PM"), make_user("Eve", "Team Member")
        project = make_project(pm)
        task = make_task(project)
        login(client, pm)
        client.post(f"/tasks/{task.id}/assign", data={"assignee_id": str(eve.id)})
        assert db.session.get(Task, task.id).assignee_id is None


def test_team_member_cannot_create_or_assign(app, client):
    with app.app_context():
        pm, tom = make_user("Pam", "PM"), make_user("Tom", "Team Member")
        project = make_project(pm, [tom])
        task = make_task(project)
        login(client, tom)
        assert client.post(f"/projects/{project.id}/tasks",
                           data={"title": "x", "priority": "Low"}).status_code == 403
        assert client.post(f"/tasks/{task.id}/assign",
                           data={"assignee_id": str(tom.id)}).status_code == 403


# ---- BL-21 My Tasks ---------------------------------------------------------
def test_my_tasks_sorted_by_due_date_and_only_mine(app, client):
    with app.app_context():
        pm, tom = make_user("Pam", "PM"), make_user("Tom", "Team Member")
        project = make_project(pm, [tom])
        today = date.today()
        make_task(project, "Later", tom, today + timedelta(days=9))
        make_task(project, "Soon", tom, today + timedelta(days=1))
        make_task(project, "NoDate", tom, None)
        make_task(project, "NotMine", pm, today)
        login(client, tom)
        html = client.get("/my-tasks").get_data(as_text=True)
        assert "NotMine" not in html
        assert html.index("Soon") < html.index("Later") < html.index("NoDate")


# ---- BL-22 status / BL-23 dashboard / BL-24 overdue ---------------------------
def test_assignee_updates_status_but_others_cannot(app, client):
    with app.app_context():
        pm, tom, ann = (make_user("Pam", "PM"), make_user("Tom", "Team Member"),
                        make_user("Ann", "Team Member"))
        project = make_project(pm, [tom, ann])
        task = make_task(project, assignee=tom)
        login(client, ann)
        assert client.post(f"/tasks/{task.id}/status",
                           data={"status": "Done"}).status_code == 403
        client.get("/logout")
        login(client, tom)
        client.post(f"/tasks/{task.id}/status", data={"status": "In Progress"})
        assert db.session.get(Task, task.id).status == "In Progress"
        client.post(f"/tasks/{task.id}/status", data={"status": "Bogus"})
        assert db.session.get(Task, task.id).status == "In Progress"


def test_dashboard_shows_40_percent(app, client):
    with app.app_context():
        pm = make_user("Pam", "PM")
        project = make_project(pm)
        for i in range(10):
            make_task(project, f"T{i}", status="Done" if i < 4 else "To Do")
        login(client, pm)
        html = client.get("/dashboard").get_data(as_text=True)
        assert "40% complete" in html
        assert task_service.percent_complete(project.tasks) == 40


def test_overdue_flagged_on_list_and_dashboard(app, client):
    with app.app_context():
        pm = make_user("Pam", "PM")
        project = make_project(pm)
        make_task(project, "Late", due=date.today() - timedelta(days=2))
        make_task(project, "LateButDone", due=date.today() - timedelta(days=2),
                  status="Done")
        login(client, pm)
        assert client.get(f"/projects/{project.id}").get_data(
            as_text=True).count("badge bg-danger\">Overdue") == 1
        assert "Overdue: 1" in client.get("/dashboard").get_data(as_text=True)


def test_is_overdue_rules():
    class T:
        pass
    t = T()
    t.due_date, t.status = date(2026, 1, 1), "To Do"
    assert task_service.is_overdue(t, date(2026, 1, 2))
    assert not task_service.is_overdue(t, date(2026, 1, 1))
    t.status = "Done"
    assert not task_service.is_overdue(t, date(2026, 1, 2))


# ---- BL-35 HTTPS -------------------------------------------------------------
def test_http_redirects_to_https_when_forced():
    from app import create_app
    app = create_app({"TESTING": True, "FORCE_HTTPS": True,
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code == 301 and resp.headers["Location"].startswith("https://")
    secure = client.get("/login", base_url="https://localhost")
    assert secure.status_code == 200
    assert "Strict-Transport-Security" in secure.headers
