"""BL-20: a PM can reassign a task; the old assignee loses it; change logged."""
from types import SimpleNamespace

from app.extensions import db
from app.models import ActivityLog, Task
from app.services import task_service
from sprint2_crud_helpers import (login, make_project, make_task,
                                make_user)


def _setup():
    pm = make_user("Pam", "PM")
    ann, bob = make_user("Ann"), make_user("Bob")
    project = make_project(pm, [ann, bob])
    return pm, ann, bob, make_task(project, assignee=ann)


def test_reassign_moves_task_and_logs_change(app, client):
    with app.app_context():
        pm, ann, bob, task = _setup()
        login(client, pm)
        resp = client.post(f"/tasks/{task.id}/assign",
                           data={"assignee_id": str(bob.id)})
        assert resp.status_code == 302
        assert db.session.get(Task, task.id).assignee_id == bob.id
        assert Task.query.filter_by(assignee_id=ann.id).count() == 0
        entry = ActivityLog.query.filter(
            ActivityLog.action.like("task reassigned%")).one()
        assert "Ann" in entry.action and "Bob" in entry.action
        assert entry.entity_id == task.id
        ann_client = app.test_client()
        login(ann_client, ann)
        assert "Task one" not in ann_client.get("/my-tasks").get_data(
            as_text=True)


def test_same_assignee_is_not_logged_again(app, client):
    with app.app_context():
        pm, ann, _bob, task = _setup()
        login(client, pm)
        client.post(f"/tasks/{task.id}/assign",
                    data={"assignee_id": str(ann.id)})
        assert ActivityLog.query.filter(
            ActivityLog.action.like("task%assigned%")).count() == 0


def test_unassign_is_logged(app, client):
    with app.app_context():
        pm, ann, _bob, task = _setup()
        login(client, pm)
        client.post(f"/tasks/{task.id}/assign", data={"assignee_id": ""})
        assert db.session.get(Task, task.id).assignee_id is None
        assert ActivityLog.query.filter(
            ActivityLog.action.like("task unassigned%")).count() == 1


def test_team_member_and_non_member_cannot_reassign(app, client):
    with app.app_context():
        pm, ann, bob, task = _setup()
        eve = make_user("Eve")
        login(client, ann)
        assert client.post(f"/tasks/{task.id}/assign",
                           data={"assignee_id": str(bob.id)}).status_code == 403
        pm_client = app.test_client()
        login(pm_client, pm)
        pm_client.post(f"/tasks/{task.id}/assign",
                       data={"assignee_id": str(eve.id)})   # not a member
        assert db.session.get(Task, task.id).assignee_id == ann.id


def test_assignment_log_text():
    a, b = SimpleNamespace(name="Ann"), SimpleNamespace(name="Bob")
    assert task_service.assignment_log_text(a, b) == \
        "task reassigned: Ann -> Bob"
    assert task_service.assignment_log_text(None, b) == "task assigned to Bob"
    assert task_service.assignment_log_text(a, None) == \
        "task unassigned (was Ann)"
    long = SimpleNamespace(name="x" * 200)
    assert len(task_service.assignment_log_text(long, b)) <= 100
