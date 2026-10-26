"""UI layer for authentication: register, login, logout (BL-05, 06, 07)."""
from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)

from app.auth_utils import load_current_user
from app.extensions import db
from app.models import ActivityLog, User
from app.services import auth_service

bp = Blueprint("auth", __name__)

SELF_REGISTER_ROLES = ("PM", "Team Member")   # Admin accounts: create_admin.py


@bp.before_app_request
def _load_user():
    load_current_user()                       # sets g.user on every request


@bp.app_context_processor
def _inject_user():
    return {"current_user": g.get("user")}


def _log(user_id, action):
    db.session.add(ActivityLog(user_id=user_id, action=action,
                               entity="User", entity_id=user_id))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "Team Member")

        problems = auth_service.validate_registration(name, email, password)
        if role not in SELF_REGISTER_ROLES:
            problems.append("Choose a valid role.")
        if not problems and User.query.filter_by(email=email).first():
            problems.append("An account with this email already exists.")

        if problems:
            for p in problems:
                flash(p, "danger")
            return render_template("register.html", name=name, email=email,
                                   role=role)

        user = User(name=name, email=email, role=role,
                    password_hash=auth_service.hash_password(password))
        db.session.add(user)
        db.session.commit()
        _log(user.id, "registered")
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        was_locked = user is not None and auth_service.is_locked(user)
        ok, message = auth_service.authenticate(user, password)
        if user is not None:
            if not ok and not was_locked and auth_service.is_locked(user):
                _log(user.id, "account locked after failed logins")
            elif not ok and not was_locked and user.is_active:
                _log(user.id, "failed login")
            db.session.commit()

        if not ok:
            flash(message, "danger")
            return render_template("login.html", email=email)

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        _log(user.id, "logged in")
        db.session.commit()
        return redirect(url_for("dashboard.home"))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
