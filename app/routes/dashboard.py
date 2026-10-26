"""Progress dashboard (BL-23)."""
from flask import Blueprint, g, render_template

from app.auth_utils import login_required, visible_projects
from app.models import STATUSES
from app.services import task_service

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def home():
    summaries = [task_service.project_summary(p)
                 for p in visible_projects(g.user).all()]
    return render_template("dashboard.html", summaries=summaries,
                           statuses=STATUSES)
