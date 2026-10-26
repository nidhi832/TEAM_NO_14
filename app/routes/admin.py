"""UI layer: admin pages (BL-27 user accounts, BL-28 activity log)."""
from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)

from app.auth_utils import roles_required
from app.models import ROLES
from app.services import admin_service, audit_service

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/users")
@roles_required("Admin")
def users():
    return render_template("admin_users.html", users=admin_service.all_users(),
                           roles=ROLES, me=g.user)


@bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@roles_required("Admin")
def deactivate(user_id):
    error = admin_service.set_active(g.user, user_id, False)
    flash(error or "Account deactivated.", "danger" if error else "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@roles_required("Admin")
def reactivate(user_id):
    error = admin_service.set_active(g.user, user_id, True)
    flash(error or "Account reactivated.", "danger" if error else "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/role", methods=["POST"])
@roles_required("Admin")
def change_role(user_id):
    error = admin_service.set_role(g.user, user_id,
                                   request.form.get("role", ""))
    flash(error or "Role updated.", "danger" if error else "success")
    return redirect(url_for("admin.users"))


@bp.route("/log")
@roles_required("Admin")
def activity_log():
    security_only = request.args.get("security") == "1"
    return render_template("admin_log.html", security_only=security_only,
                           entries=audit_service.recent(
                               security_only=security_only))
