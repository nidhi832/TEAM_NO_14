"""BL-31 usability: a new user can create a project and assign a task fast.

The 10-minute / 5-of-5 target is measured with real people (see
docs/testing/usability-test.md). These tests protect what makes that possible:
the journey needs only a few steps and every page shows the way to the next one.
"""
from app.extensions import db
from app.models import Project, Task, User
from sprint2_crud_helpers import PASSWORD, login, make_project, make_user

MAX_STEPS = 8   # register, log in, open form, create project, create task,
                # check My Tasks = 6 requests, with room to spare


def test_new_pm_can_create_project_and_assign_task_in_few_steps(app, client):
    steps = []

    def visit(method, url, **kwargs):
        steps.append((method, url))
        return getattr(client, method)(url, follow_redirects=True, **kwargs)

    with app.app_context():
        resp = visit("post", "/register", data={
            "name": "Nina New", "email": "nina@new.test",
            "password": PASSWORD, "role": "PM"})
        assert b"Account created" in resp.data

        resp = visit("post", "/login", data={
            "email": "nina@new.test", "password": PASSWORD})
        assert resp.status_code == 200
        assert b"/projects/new" in resp.data       # dashboard offers the next step

        resp = visit("get", "/projects/new")
        assert resp.status_code == 200

        resp = visit("post", "/projects/new", data={"name": "First project"})
        assert b"Project created" in resp.data
        assert b"next-step-hint" in resp.data      # tells a new PM what to do next
        assert b"add-task-section" in resp.data    # and where the form is

        project = Project.query.filter_by(name="First project").one()
        nina = User.query.filter_by(email="nina@new.test").one()
        resp = visit("post", f"/projects/{project.id}/tasks", data={
            "title": "Prepare report", "priority": "Medium",
            "assignee_id": str(nina.id)})
        assert b"Task created" in resp.data
        assert b"Prepare report" in resp.data
        assert b"next-step-hint" not in resp.data  # hint goes away once used

        resp = visit("get", "/my-tasks")
        assert b"Prepare report" in resp.data
        assert Task.query.one().assignee_id == nina.id

    assert len(steps) <= MAX_STEPS


def test_pm_can_assign_task_to_invited_teammate(app, client):
    with app.app_context():
        pm = make_user("Pam", "PM")
        mate = make_user("Tom")
        login(client, pm)
        client.post("/projects/new", data={"name": "Team work"})
        project = Project.query.filter_by(name="Team work").one()

        resp = client.post(f"/projects/{project.id}/members",
                           data={"email": mate.email}, follow_redirects=True)
        assert b"added to the project" in resp.data

        resp = client.post(f"/projects/{project.id}/tasks", data={
            "title": "Review design", "priority": "High",
            "assignee_id": str(mate.id)}, follow_redirects=True)
        assert b"Task created" in resp.data
        assert Task.query.one().assignee_id == mate.id


def test_register_page_explains_which_role_creates_projects(client):
    resp = client.get("/register")
    assert b"role-help" in resp.data
    assert b"Choose <strong>Project Manager</strong>" in resp.data


def test_team_member_is_told_what_to_do_instead_of_seeing_a_dead_end(app, client):
    with app.app_context():
        login(client, make_user("Tom"))
        resp = client.get("/dashboard")
        assert b"Contact your Project Manager" in resp.data


def test_assignee_help_changes_when_teammates_join(app, client):
    with app.app_context():
        pm = make_user("Pam", "PM")
        mate = make_user("Tom")
        project = make_project(pm)
        login(client, pm)

        resp = client.get(f"/projects/{project.id}")
        assert b"Only you are in this project so far" in resp.data

        project.members.append(mate)
        db.session.commit()
        resp = client.get(f"/projects/{project.id}")
        assert b"Only project members can be assigned." in resp.data
        assert b"Only you are in this project so far" not in resp.data
