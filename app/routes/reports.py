"""UI layer: task filter/search and CSV progress report (BL-25, BL-26)."""
from datetime import date

from flask import (Blueprint, Response, abort, flash, g, render_template,
                   request)

from app.auth_utils import get_project_or_403, login_required, visible_projects
from app.models import PRIORITIES, STATUSES
from app.services import report_service, task_service

bp = Blueprint("reports", __name__)


@bp.route("/tasks/search")
@login_required
def search():
    filters, errors = report_service.parse_filters(request.args)
    for e in errors:
        flash(e, "danger")
    return render_template(
        "task_search.html", filters=filters,
        tasks=report_service.search_tasks(g.user, filters),
        statuses=STATUSES, priorities=PRIORITIES,
        projects=visible_projects(g.user).all(),
        assignees=report_service.assignee_choices(g.user),
        is_overdue=task_service.is_overdue, today=date.today())


@bp.route("/projects/<int:project_id>/report.csv")
@login_required
def project_report(project_id):
    project = get_project_or_403(project_id)       # 404 / 403 for outsiders
    if not report_service.can_download_report(g.user, project):
        abort(403)
    filename = f"project_{project.id}_progress_{date.today().isoformat()}.csv"
    return Response(report_service.project_report_csv(project),
                    mimetype="text/csv",
                    headers={"Content-Disposition":
                             f"attachment; filename={filename}"})
