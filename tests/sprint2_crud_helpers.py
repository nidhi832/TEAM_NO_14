"""Small helpers shared by the BL-11/12/16/17/18 tests."""
from app.extensions import db
from app.models import Project, Task, User
from app.services import auth_service

PASSWORD = "Passw0rdX"


def make_user(name, role="Team Member"):
    user = User(name=name, email=f"{name.lower()}@crud.test", role=role,
                password_hash=auth_service.hash_password(PASSWORD))
    db.session.add(user)
    db.session.commit()
    return user


def login(client, user):
    client.post("/login", data={"email": user.email, "password": PASSWORD})


def make_project(owner, members=(), name="Demo"):
    project = Project(name=name, owner_id=owner.id)
    project.members.append(owner)
    for member in members:
        project.members.append(member)
    db.session.add(project)
    db.session.commit()
    return project


def make_task(project, title="Task one", assignee=None):
    task = Task(project_id=project.id, title=title,
                assignee_id=assignee.id if assignee else None)
    db.session.add(task)
    db.session.commit()
    return task
