"""BL-11: a PM can edit project details."""
from app.extensions import db
from app.models import ActivityLog, Project
from sprint2_crud_helpers import login, make_project, make_user


def test_pm_edits_project_and_it_persists(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm).id
        login(client, pm)
        resp = client.post(f"/projects/{project_id}/edit", data={
            "name": "Renamed", "description": "New text",
            "start_date": "2026-10-01", "end_date": "2026-10-30"})
        assert resp.status_code == 302
        page = client.get(f"/projects/{project_id}")      # reload
        assert b"Renamed" in page.data
        project = db.session.get(Project, project_id)
        assert project.description == "New text"
        assert str(project.end_date) == "2026-10-30"


def test_edit_form_is_prefilled(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Prefilled").id
        login(client, pm)
        resp = client.get(f"/projects/{project_id}/edit")
        assert resp.status_code == 200
        assert b"Prefilled" in resp.data


def test_end_date_before_start_is_rejected(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Keep me").id
        login(client, pm)
        resp = client.post(f"/projects/{project_id}/edit", data={
            "name": "Changed", "start_date": "2026-10-30",
            "end_date": "2026-10-01"})
        assert resp.status_code == 400
        assert db.session.get(Project, project_id).name == "Keep me"


def test_blank_name_is_rejected(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Keep me").id
        login(client, pm)
        resp = client.post(f"/projects/{project_id}/edit",
                           data={"name": "  "})
        assert resp.status_code == 400
        assert db.session.get(Project, project_id).name == "Keep me"


def test_member_and_other_pm_cannot_edit(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        other_pm = make_user("Olga", "PM")
        member = make_user("Mia")
        project_id = make_project(pm, [member, other_pm]).id
        for user in (member, other_pm):
            login(client, user)
            url = f"/projects/{project_id}/edit"
            assert client.get(url).status_code == 403
            assert client.post(url, data={"name": "Hacked"}).status_code == 403
        assert db.session.get(Project, project_id).name == "Demo"


def test_non_member_gets_403(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        outsider = make_user("Omar")
        project_id = make_project(pm).id
        login(client, outsider)
        assert client.get(f"/projects/{project_id}/edit").status_code == 403


def test_edit_is_logged(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm).id
        login(client, pm)
        client.post(f"/projects/{project_id}/edit", data={"name": "Logged"})
        entry = ActivityLog.query.filter_by(action="project edited").one()
        assert entry.entity_id == project_id
