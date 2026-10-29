"""BL-16: a PM can edit a task; changes are saved and logged."""
from datetime import date

from app.extensions import db
from app.models import ActivityLog, Task
from sprint2_crud_helpers import login, make_project, make_task, make_user


def test_pm_edits_task_and_changes_are_saved(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        resp = client.post(f"/tasks/{task_id}/edit", data={
            "title": "Better title", "description": "More detail",
            "priority": "High", "due_date": "2026-10-30"})
        assert resp.status_code == 302
        task = db.session.get(Task, task_id)
        assert task.title == "Better title"
        assert task.description == "More detail"
        assert task.priority == "High"
        assert task.due_date == date(2026, 10, 30)


def test_edit_is_logged(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/edit",
                    data={"title": "Logged", "priority": "Low"})
        entry = ActivityLog.query.filter_by(action="task edited").one()
        assert entry.entity_id == task_id
        assert entry.user_id == pm.id


def test_edit_form_is_prefilled(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm), title="Prefilled").id
        login(client, pm)
        resp = client.get(f"/tasks/{task_id}/edit")
        assert resp.status_code == 200
        assert b"Prefilled" in resp.data


def test_invalid_edit_is_rejected_and_nothing_changes(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm), title="Keep me").id
        login(client, pm)
        for data in ({"title": " ", "priority": "Low"},
                     {"title": "X", "priority": "Urgent"},
                     {"title": "X", "priority": "Low", "due_date": "bad"}):
            assert client.post(f"/tasks/{task_id}/edit",
                               data=data).status_code == 400
        assert db.session.get(Task, task_id).title == "Keep me"


def test_member_cannot_edit_task(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        member = make_user("Mia")
        task_id = make_task(make_project(pm, [member]), assignee=member).id
        login(client, member)
        url = f"/tasks/{task_id}/edit"
        assert client.get(url).status_code == 403
        resp = client.post(url, data={"title": "Hacked", "priority": "Low"})
        assert resp.status_code == 403
        assert db.session.get(Task, task_id).title == "Task one"


def test_non_member_gets_403_and_missing_task_404(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        outsider = make_user("Omar")
        task_id = make_task(make_project(pm)).id
        login(client, outsider)
        assert client.get(f"/tasks/{task_id}/edit").status_code == 403
        assert client.get("/tasks/9999/edit").status_code == 404
