"""BL-17: a PM can delete a task, only after confirmation."""
from app.extensions import db
from app.models import ActivityLog, Comment, Task
from sprint2_crud_helpers import login, make_project, make_task, make_user


def test_get_shows_confirmation_and_does_not_delete(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm), title="Precious").id
        login(client, pm)
        resp = client.get(f"/tasks/{task_id}/delete")
        assert resp.status_code == 200
        assert b"Precious" in resp.data
        assert b"Delete this task?" in resp.data
        assert db.session.get(Task, task_id) is not None


def test_post_after_confirmation_deletes_task_and_comments(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project = make_project(pm)
        task_id = make_task(project).id
        db.session.add(Comment(task_id=task_id, user_id=pm.id, text="hi"))
        db.session.commit()
        login(client, pm)
        resp = client.post(f"/tasks/{task_id}/delete")
        assert resp.status_code == 302
        assert db.session.get(Task, task_id) is None
        assert Comment.query.filter_by(task_id=task_id).count() == 0


def test_deleted_task_disappears_from_project_page(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        project = make_project(pm)
        project_id = project.id
        task_id = make_task(project, title="Vanishing").id
        login(client, pm)
        assert b"Vanishing" in client.get(f"/projects/{project_id}").data
        client.post(f"/tasks/{task_id}/delete")
        assert b"Vanishing" not in client.get(f"/projects/{project_id}").data


def test_delete_is_logged(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/delete")
        entry = ActivityLog.query.filter_by(action="task deleted").one()
        assert entry.entity_id == task_id
        assert entry.user_id == pm.id


def test_member_cannot_delete_task(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        member = make_user("Mia")
        task_id = make_task(make_project(pm, [member]), assignee=member).id
        login(client, member)
        url = f"/tasks/{task_id}/delete"
        assert client.get(url).status_code == 403
        assert client.post(url).status_code == 403
        assert db.session.get(Task, task_id) is not None


def test_non_member_and_missing_task(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        outsider = make_user("Omar")
        task_id = make_task(make_project(pm)).id
        login(client, outsider)
        assert client.post(f"/tasks/{task_id}/delete").status_code == 403
        assert client.post("/tasks/9999/delete").status_code == 404
        assert db.session.get(Task, task_id) is not None
