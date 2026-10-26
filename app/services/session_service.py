"""BUSINESS layer: session tokens, idle timeout and logout (BL-09, BL-39)."""
import secrets
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import User
from app.models_session import UserSession

IDLE_MINUTES = 30
TOUCH_SECONDS = 60   # refresh last_seen at most once a minute (BL-29 speed)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def start_session(user_id, now=None):
    """Create a new random token for a fresh login and return it."""
    now = now or utcnow()
    token = secrets.token_urlsafe(32)
    db.session.add(UserSession(token=token, user_id=user_id,
                               created_at=now, last_seen=now))
    db.session.commit()
    return token


def check_session(token, user_id, idle_minutes=IDLE_MINUTES, now=None):
    """Return "ok", "expired", "revoked" or "inactive".

    "ok" also refreshes last_seen (at most once a minute, to save database
    writes), so only real inactivity ends the session.
    """
    now = now or utcnow()
    record = UserSession.query.filter_by(token=token).first() if token else None
    if record is None or record.user_id != user_id or record.revoked:
        return "revoked"
    if now - record.last_seen > timedelta(minutes=idle_minutes):
        record.revoked = True
        db.session.commit()
        return "expired"
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        record.revoked = True
        db.session.commit()
        return "inactive"
    if now - record.last_seen >= timedelta(seconds=TOUCH_SECONDS):
        record.last_seen = now          # skip the DB write on most requests
        db.session.commit()
    return "ok"


def end_session(token):
    """Invalidate a token (logout). Returns True if it was active."""
    record = UserSession.query.filter_by(token=token).first() if token else None
    if record is None or record.revoked:
        return False
    record.revoked = True
    db.session.commit()
    return True
