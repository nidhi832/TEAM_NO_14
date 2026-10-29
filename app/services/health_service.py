"""BUSINESS layer: is the system able to serve requests? (BL-30)"""
from sqlalchemy import text

from app.extensions import db


def database_ok():
    """True when the database answers a trivial query."""
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:           # any failure means "not available"
        db.session.rollback()
        return False


def status():
    """Returns (body, http_status) for the /health endpoint."""
    ok = database_ok()
    body = {"status": "ok" if ok else "error",
            "database": "ok" if ok else "unavailable"}
    return body, 200 if ok else 503
