import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Project, Task, User


def make_user(email="a@example.com", role="PM"):
    return User(name="Test", email=email, password_hash="x", role=role)


def test_home_page_loads(client):
    assert client.get("/").status_code == 200


def test_all_tables_exist(app):
    expected = {"users", "projects", "project_members", "tasks",
                "comments", "activity_logs"}
    assert expected <= set(db.metadata.tables)


def test_user_defaults(app):
    with app.app_context():
        user = make_user()
        db.session.add(user)
        db.session.commit()
        assert user.is_active is True
        assert user.failed_attempts == 0
        assert user.locked_until is None


def test_email_must_be_unique(app):
    with app.app_context():
        db.session.add(make_user())
        db.session.commit()
        db.session.add(make_user())
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_project_task_relationships(app):
    with app.app_context():
        pm = make_user()
        db.session.add(pm)
        db.session.commit()
        project = Project(name="P1", owner_id=pm.id)
        project.members.append(pm)
        db.session.add(project)
        db.session.commit()
        task = Task(project_id=project.id, title="T1", assignee_id=pm.id)
        db.session.add(task)
        db.session.commit()
        assert task.status == "To Do"
        assert task.project.name == "P1"
        assert project.members[0].email == "a@example.com"
