"""BL-38: reject oversized input and keep query/XSS payloads safe."""
from app.extensions import db
from app.models import Project, Task, User
from app.services import auth_service, project_service
from sprint2_crud_helpers import login, make_project, make_task, make_user


def test_registration_rejects_oversized_name_and_email(app, client):
    resp = client.post("/register", data={
        "name": "N" * 101, "email": "a" * 115 + "@x.test",
        "password": "Passw0rdX"})
    assert b"100 characters or fewer" in resp.data or b"valid email" in resp.data
    with app.app_context():
        assert User.query.count() == 0


def test_project_and_task_length_limits():
    problems, _, _ = project_service.validate_project("P" * 121, "", "")
    assert any("120 characters" in p for p in problems)
    problems, _ = project_service.validate_task("T" * 151, "High", "")
    assert any("150 characters" in p for p in problems)


def test_oversized_project_description_is_rejected(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        login(client, pm)
        resp = client.post("/projects/new", data={
            "name": "Project", "description": "x" * 5001})
        assert resp.status_code == 400
        assert Project.query.count() == 0


def test_search_injection_is_treated_as_literal_text(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project = make_project(pm)
        make_task(project, title="Ordinary task")
        login(client, pm)
        resp = client.get("/tasks/search?q=%27%20OR%201%3D1--")
        assert b"Ordinary task" not in resp.data


def test_task_title_is_html_escaped_on_project_page(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project = make_project(pm)
        make_task(project, title="<script>alert(1)</script>")
        login(client, pm)
        page = client.get(f"/projects/{project.id}").get_data(as_text=True)
        assert "<script>alert(1)</script>" not in page
        assert "&lt;script&gt;" in page
