"""BL-12: a PM can archive a finished project."""
from app.extensions import db
from app.models import ActivityLog, Project
from sprint2_crud_helpers import login, make_project, make_user


def test_archived_project_hidden_from_active_list(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Old Project").id
        login(client, pm)
        assert b"Old Project" in client.get("/projects").data
        resp = client.post(f"/projects/{project_id}/archive")
        assert resp.status_code == 302
        assert db.session.get(Project, project_id).archived is True
        assert b"Old Project" not in client.get("/projects").data


def test_archived_project_is_retrievable(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Old Project").id
        login(client, pm)
        client.post(f"/projects/{project_id}/archive")
        listing = client.get("/projects/archived")
        assert listing.status_code == 200
        assert b"Old Project" in listing.data
        assert client.get(f"/projects/{project_id}").status_code == 200


def test_restore_puts_project_back(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm, name="Old Project").id
        login(client, pm)
        client.post(f"/projects/{project_id}/archive")
        client.post(f"/projects/{project_id}/unarchive")
        assert b"Old Project" in client.get("/projects").data
        assert b"Old Project" not in client.get("/projects/archived").data


def test_member_cannot_archive_or_restore(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        member = make_user("Mia")
        project_id = make_project(pm, [member]).id
        login(client, member)
        assert client.post(
            f"/projects/{project_id}/archive").status_code == 403
        assert client.post(
            f"/projects/{project_id}/unarchive").status_code == 403
        assert db.session.get(Project, project_id).archived is False


def test_archived_list_only_shows_own_projects(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        other = make_user("Olga", "PM")
        make_project(other, name="Secret").archived = True
        db.session.commit()
        login(client, pm)
        assert b"Secret" not in client.get("/projects/archived").data


def test_archive_and_restore_are_logged(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project_id = make_project(pm).id
        login(client, pm)
        client.post(f"/projects/{project_id}/archive")
        client.post(f"/projects/{project_id}/unarchive")
        actions = {a.action for a in ActivityLog.query.all()}
        assert {"project archived", "project restored"} <= actions
