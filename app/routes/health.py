"""UI layer: health check used by the uptime monitor (BL-30, MPMS-NF-002).

No login needed on purpose, so a monitor can poll it. It returns only
"ok"/"error", never details about the system.
"""
from flask import Blueprint, jsonify

from app.services import health_service

bp = Blueprint("health", __name__)


@bp.route("/health")
def health():
    body, code = health_service.status()
    response = jsonify(body)
    response.status_code = code
    response.headers["Cache-Control"] = "no-store"
    return response
