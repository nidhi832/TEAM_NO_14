"""Server-side session checks for every request (BL-09, BL-39, BL-40).

- each login gets a random token stored in the user_sessions table
- 30 minutes without a request ends the session (BL-09)
- logout revokes the token, so a copied old cookie stops working (BL-39)
- logouts and idle timeouts are written to the activity log (BL-40)
"""
from flask import flash, g, redirect, request, session, url_for

from app.services import audit_service, session_service

MESSAGES = {
    "expired": "Your session expired after 30 minutes of inactivity. "
               "Please log in again.",
    "revoked": "Your session is no longer valid. Please log in again.",
    "inactive": "Your account has been deactivated.",
}


def init_session_security(app):
    app.config.setdefault("SESSION_IDLE_MINUTES", session_service.IDLE_MINUTES)

    @app.before_request
    def _check_session_token():
        if request.endpoint == "static":
            return None
        user_id = session.get("user_id")
        token = session.get("sid")

        # logging out, or logging in again: revoke the old token first
        if request.endpoint == "auth.logout" or (
                request.endpoint == "auth.login" and request.method == "POST"):
            if session_service.end_session(token) and user_id and \
                    request.endpoint == "auth.logout":
                audit_service.log_security_event(user_id, "logged out", user_id)
            session.pop("sid", None)
            return None

        if not user_id:
            return None
        if not token:                       # first request after login
            session["sid"] = session_service.start_session(user_id)
            return None

        status = session_service.check_session(
            token, user_id, app.config["SESSION_IDLE_MINUTES"])
        if status == "ok":
            return None
        if status == "expired":
            audit_service.log_security_event(
                user_id, "session expired after inactivity", user_id)
        session.clear()
        g.user = None
        flash(MESSAGES[status], "warning")
        if request.endpoint in ("auth.login", "auth.register"):
            return None
        return redirect(url_for("auth.login"))
