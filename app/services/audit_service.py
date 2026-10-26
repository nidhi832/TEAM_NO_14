"""BUSINESS layer: activity log and security events (BL-28, BL-40).

Teammates: call log_event(...) after every create/edit/delete/assign, and
log_security_event(...) for deletions, so they show up on /admin/log.
"""
from app.extensions import db
from app.models import ActivityLog, User

SECURITY = "Security"


def log_event(user_id, action, entity=None, entity_id=None, commit=True):
    db.session.add(ActivityLog(user_id=user_id, action=action,
                               entity=entity, entity_id=entity_id))
    if commit:
        db.session.commit()


def log_security_event(user_id, action, entity_id=None, commit=True):
    log_event(user_id, action, SECURITY, entity_id, commit)


SECURITY_WORDS = ("login", "locked", "logged", "session", "role",
                  "deactivated", "reactivated", "deleted")


def recent(limit=200, security_only=False):
    """Newest first, as (entry, user_name) pairs.
    security_only also includes auth events logged by BL-06/07."""
    query = (db.session.query(ActivityLog, User.name)
             .outerjoin(User, ActivityLog.user_id == User.id))
    if security_only:
        word_filters = [ActivityLog.action.ilike(f"%{w}%")
                        for w in SECURITY_WORDS]
        query = query.filter(db.or_(ActivityLog.entity == SECURITY,
                                    *word_filters))
    return (query.order_by(ActivityLog.created_at.desc(),
                           ActivityLog.id.desc())
            .limit(limit).all())
