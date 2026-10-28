"""BL-37: direct requests must enforce role and project membership."""
from app.extensions import db
from app.models import Task
from sprint2_crud_helpers import login, make_project, make_task, make_user


def test_nonmember_cannot_read_project_or_download_its_report(app, client):
    with app.app_context():
        owner = make_user("Owner", "PM")
        outsider = make_user("Outsider")
        project = make_project(owner, name="Private")
        make_task(project, title="Secret task")
        login(client, outsider)
        assert client.get(f"/projects/{project.id}").status_code == 403
        assert client.get(f"/projects/{project.id}/report.csv").status_code == 403
        search = client.get("/tasks/search?q=Secret")
        assert b"Secret task" not in search.data


def test_member_cannot_manage_project_or_reassign_task(app, client):
    with app.app_context():
        owner = make_user("Owner", "PM")
        member = make_user("Member")
        project = make_project(owner, [member])
        task = make_task(project, assignee=member)
        login(client, member)
        assert client.get(f"/projects/{project.id}/edit").status_code == 403
        assert client.post(f"/projects/{project.id}/members",
                           data={"email": "outsider@example.test"}).status_code == 403
        assert client.post(f"/tasks/{task.id}/assign",
                           data={"assignee_id": ""}).status_code == 403
        assert db.session.get(Task, task.id).assignee_id == member.id


def test_task_status_is_restricted_to_assignee_or_project_manager(app, client):
    with app.app_context():
        owner = make_user("Owner", "PM")
        member = make_user("Member")
        other = make_user("Other")
        project = make_project(owner, [member, other])
        task = make_task(project, assignee=member)
        login(client, other)
        assert client.post(f"/tasks/{task.id}/status",
                           data={"status": "Done"}).status_code == 403
        assert db.session.get(Task, task.id).status == "To Do"


def test_admin_can_access_project_and_edit_it(app, client):
    with app.app_context():
        owner = make_user("Owner", "PM")
        admin = make_user("AdminUser", "Admin")
        project = make_project(owner)
        login(client, admin)
        assert client.get(f"/projects/{project.id}").status_code == 200
        assert client.get(f"/projects/{project.id}/edit").status_code == 200
