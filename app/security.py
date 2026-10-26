"""HTTPS / TLS settings (BL-35, PRJ-SR-001).

Off by default so `python run.py` works on localhost. In production set the
environment variable FORCE_HTTPS=1 (or config FORCE_HTTPS=True): HTTP requests
are redirected to HTTPS, cookies get the Secure flag and HSTS is sent.
TLS 1.2+ itself is enforced by the web server / reverse proxy in front.
"""
import os

from flask import redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix


def init_security(app):
    if os.environ.get("FORCE_HTTPS") == "1":
        app.config.setdefault("FORCE_HTTPS", True)
    app.config.setdefault("FORCE_HTTPS", False)

    # trust X-Forwarded-Proto from a reverse proxy (Render, Nginx, ...)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    if app.config["FORCE_HTTPS"]:
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    @app.before_request
    def _redirect_to_https():
        if app.config["FORCE_HTTPS"] and not request.is_secure:
            return redirect(request.url.replace("http://", "https://", 1),
                            code=301)

    @app.after_request
    def _security_headers(response):
        if app.config["FORCE_HTTPS"]:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response
