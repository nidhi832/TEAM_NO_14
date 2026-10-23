"""DATA layer: all database tables (BL-03)."""
from datetime import datetime, timezone

from app.extensions import db

ROLES = ("Admin", "PM", "Team Member")
STATUSES = ("To Do", "In Progress", "In Review", "Done")
PRIORITIES = ("Low", "Medium", "High")


def _now():
    return datetime.now(timezone.utc)


# many-to-many link between projects and users
project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"),
              primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"),
              primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Team Member")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                         nullable=False)
    archived = db.Column(db.Boolean, nullable=False, default=False)

    owner = db.relationship("User", foreign_keys=[owner_id])
    members = db.relationship("User", secondary=project_members,
                              backref="projects")
    tasks = db.relationship("Task", backref="project",
                            cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"),
                           nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default="To Do")
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                            nullable=True)

    assignee = db.relationship("User", foreign_keys=[assignee_id])
    comments = db.relationship("Comment", backref="task",
                               cascade="all, delete-orphan")


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"),
                        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)

    user = db.relationship("User")


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)
