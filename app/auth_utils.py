"""Access control helpers shared by every module (BL-08, BL-14, BL-37).

Uses the session keys set by the login route: user_id, user_name, role.
"""
from functools import wraps

from flask import abort, g, redirect, request, session, url_for

from app.extensions import db
from app.models import ActivityLog, Project, User


def load_current_user():
    """Runs before every request: sets g.user (or None)."""
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None
    if g.user is not None and not g.user.is_active:     # deactivated meanwhile
        session.clear()
        g.user = None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    """BL-08: only the listed roles can use the route (Admin can use all).

        @bp.route("/projects/new")
        @roles_required("PM")
    """
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.role != "Admin" and g.user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ---- project access (BL-14, BL-37 later) ---------------------------------
def visible_projects(user, include_archived=False):
    """BL-14: only projects the user owns or belongs to (Admin sees all)."""
    query = Project.query
    if user.role != "Admin":
        query = query.filter((Project.owner_id == user.id)
                             | Project.members.any(User.id == user.id))
    if not include_archived:
        query = query.filter(Project.archived.is_(False))
    return query.order_by(Project.id.desc())


def can_view_project(user, project):
    return (user.role == "Admin" or project.owner_id == user.id
            or user in project.members)


def can_manage_project(user, project):
    """Owner PM (or Admin) can add members, create and assign tasks."""
    return user.role == "Admin" or (user.role == "PM"
                                    and project.owner_id == user.id)


def get_project_or_403(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        abort(404)
    if not can_view_project(g.user, project):
        abort(403)
    return project


def log_event(action, entity=None, entity_id=None):
    """Adds an activity-log row for the current user. The caller commits."""
    user_id = g.user.id if g.get("user") else None
    db.session.add(ActivityLog(user_id=user_id, action=action,
                               entity=entity, entity_id=entity_id))
