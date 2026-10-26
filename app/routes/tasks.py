"""Tasks, allocation, My Tasks, status updates (BL-15, 19, 21, 22, 24)."""
from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from app.auth_utils import (can_manage_project, can_view_project,
                            get_project_or_403, log_event, login_required)
from app.extensions import db
from app.models import STATUSES, Task, User
from app.services import project_service, task_service

bp = Blueprint("tasks", __name__)


def _safe_next(default):
    nxt = request.form.get("next", "")
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else default


def _get_task_or_403(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    if not can_view_project(g.user, task.project):
        abort(403)
    return task


def _member_or_none(project, user_id_text):
    """BL-19: only project members can be assignees. '' means unassigned."""
    if not user_id_text:
        return None, None
    user = db.session.get(User, int(user_id_text)) if user_id_text.isdigit() \
        else None
    if user is None or user not in project.members:
        return None, "Only project members can be assigned."
    return user, None


@bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
@login_required
def create_task(project_id):
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):         # BL-08
        abort(403)
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "Medium")
    problems, due = project_service.validate_task(
        title, priority, request.form.get("due_date"))
    assignee, error = _member_or_none(project, request.form.get("assignee_id", ""))
    if error:
        problems.append(error)
    if problems:
        for p in problems:
            flash(p, "danger")
    else:
        task = Task(project_id=project.id, title=title, priority=priority,
                    description=request.form.get("description", "").strip(),
                    due_date=due, status="To Do",
                    assignee_id=assignee.id if assignee else None)
        db.session.add(task)
        db.session.flush()
        log_event("task created", "Task", task.id)
        db.session.commit()
        flash("Task created.", "success")
    return redirect(url_for("projects.show_project", project_id=project.id))


@bp.route("/tasks/<int:task_id>/assign", methods=["POST"])
@login_required
def assign_task(task_id):
    task = _get_task_or_403(task_id)
    if not can_manage_project(g.user, task.project):
        abort(403)
    assignee, error = _member_or_none(task.project,
                                      request.form.get("assignee_id", ""))
    if error:
        flash(error, "danger")
    else:
        task.assignee_id = assignee.id if assignee else None
        log_event("task assigned", "Task", task.id)
        db.session.commit()
        flash("Assignment saved.", "success")
    return redirect(_safe_next(url_for("projects.show_project",
                                       project_id=task.project_id)))


@bp.route("/my-tasks")
@login_required
def my_tasks():
    tasks = Task.query.filter_by(assignee_id=g.user.id).all()
    tasks = [t for t in tasks if not t.project.archived]
    tasks.sort(key=task_service.due_sort_key)           # BL-21
    overdue_ids = {t.id for t in tasks if task_service.is_overdue(t)}
    return render_template("my_tasks.html", tasks=tasks,
                           overdue_ids=overdue_ids, statuses=STATUSES)


@bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = _get_task_or_403(task_id)
    if task.assignee_id != g.user.id and not can_manage_project(g.user,
                                                                task.project):
        abort(403)                                      # only assignee or PM
    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Choose a valid status.", "danger")
    else:
        task.status = status
        log_event(f"task status -> {status}", "Task", task.id)
        db.session.commit()
        flash("Status updated.", "success")
    return redirect(_safe_next(url_for("tasks.my_tasks")))
