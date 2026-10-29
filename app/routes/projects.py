"""Projects and project members (BL-10, 11, 12, 13, 14)."""
from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from app.auth_utils import (can_manage_project, get_project_or_403, log_event,
                            login_required, roles_required, visible_projects)
from app.extensions import db
from app.models import PRIORITIES, STATUSES, Project, Task, User
from app.services import project_service, task_service

bp = Blueprint("projects", __name__)


@bp.route("/projects")
@login_required
def list_projects():
    projects = visible_projects(g.user).all()          # BL-14
    return render_template("projects_list.html", projects=projects)


@bp.route("/projects/archived")
@login_required
def list_archived():
    """BL-12: archived projects stay retrievable here."""
    projects = (visible_projects(g.user, include_archived=True)
                .filter(Project.archived.is_(True)).all())
    return render_template("projects_archived.html", projects=projects)


@bp.route("/projects/new", methods=["GET", "POST"])
@roles_required("PM")                                  # BL-08
def new_project():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if len(description) > 5000:
            return "Project description must be 5000 characters or fewer.", 400

        problems, start, end = project_service.validate_project(
            name, request.form.get("start_date"), request.form.get("end_date"))
        if problems:
            for p in problems:
                flash(p, "danger")
            return render_template("project_new.html", form=request.form), 400

        project = Project(name=name, description=description, start_date=start,
                          end_date=end, owner_id=g.user.id)
        project.members.append(g.user)                 # owner is a member too
        db.session.add(project)
        db.session.flush()
        log_event("project created", "Project", project.id)
        db.session.commit()
        flash("Project created.", "success")
        return redirect(url_for("projects.show_project", project_id=project.id))

    return render_template("project_new.html", form={})


@bp.route("/projects/<int:project_id>")
@login_required
def show_project(project_id):
    project = get_project_or_403(project_id)
    tasks = sorted(project.tasks, key=task_service.due_sort_key)
    overdue_ids = {t.id for t in tasks if task_service.is_overdue(t)}
    return render_template(
        "project_detail.html", project=project, tasks=tasks,
        overdue_ids=overdue_ids, can_manage=can_manage_project(g.user, project),
        statuses=STATUSES, priorities=PRIORITIES,
        summary=task_service.project_summary(project))


@bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    """BL-11: the owner PM (or Admin) edits name, description, dates."""
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if len(description) > 5000:
            return "Project description must be 5000 characters or fewer.", 400

        problems, start, end = project_service.validate_project(
            name, request.form.get("start_date"), request.form.get("end_date"))
        if problems:
            for p in problems:
                flash(p, "danger")
            return render_template("project_edit.html", project=project,
                                   form=request.form), 400

        project.name = name
        project.description = description
        project.start_date = start
        project.end_date = end
        log_event("project edited", "Project", project.id)
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("projects.show_project",
                                project_id=project.id))

    form = {"name": project.name, "description": project.description or "",
            "start_date": project.start_date.isoformat()
            if project.start_date else "",
            "end_date": project.end_date.isoformat()
            if project.end_date else ""}
    return render_template("project_edit.html", project=project, form=form)


@bp.route("/projects/<int:project_id>/archive", methods=["POST"])
@login_required
def archive_project(project_id):
    """BL-12: hide a finished project from the active list."""
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):
        abort(403)
    project.archived = True
    log_event("project archived", "Project", project.id)
    db.session.commit()
    flash("Project archived. Find it under Archived projects.", "success")
    return redirect(url_for("projects.list_projects"))


@bp.route("/projects/<int:project_id>/unarchive", methods=["POST"])
@login_required
def unarchive_project(project_id):
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):
        abort(403)
    project.archived = False
    log_event("project restored", "Project", project.id)
    db.session.commit()
    flash("Project restored.", "success")
    return redirect(url_for("projects.show_project", project_id=project.id))


@bp.route("/projects/<int:project_id>/members", methods=["POST"])
@login_required
def add_member(project_id):
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):
        abort(403)

    email = request.form.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user is None or not user.is_active:
        flash("No active user with that email. They must register first.",
              "danger")
    elif user in project.members:
        flash("That user is already a member.", "warning")
    else:
        project.members.append(user)
        log_event("member added", "Project", project.id)
        db.session.commit()
        flash(f"{user.name} added to the project.", "success")

    return redirect(url_for("projects.show_project", project_id=project.id))


@bp.route("/projects/<int:project_id>/members/<int:user_id>/remove",
          methods=["POST"])
@login_required
def remove_member(project_id, user_id):
    project = get_project_or_403(project_id)
    if not can_manage_project(g.user, project):
        abort(403)

    user = db.session.get(User, user_id)
    if user is None or user not in project.members:
        abort(404)

    if user.id == project.owner_id:
        flash("The project owner cannot be removed.", "danger")
    else:
        project.members.remove(user)
        for task in Task.query.filter_by(project_id=project.id,
                                         assignee_id=user.id):
            task.assignee_id = None
        log_event("member removed", "Project", project.id)
        db.session.commit()
        flash(f"{user.name} removed from the project.", "success")

    return redirect(url_for("projects.show_project", project_id=project.id))
