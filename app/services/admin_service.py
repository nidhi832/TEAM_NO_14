"""BUSINESS layer: user account administration (BL-27, BL-40)."""
from app.extensions import db
from app.models import ROLES, User
from app.services import audit_service


def all_users():
    return User.query.order_by(User.name).all()


def set_active(admin, user_id, active):
    """Deactivate or reactivate an account. Returns an error message or None."""
    user = db.session.get(User, user_id)
    if user is None:
        return "User not found."
    if user.id == admin.id:
        return "You cannot change your own account status."
    if user.is_active == active:
        return None
    user.is_active = active
    if active:
        user.failed_attempts = 0
        user.locked_until = None
    word = "reactivated" if active else "deactivated"
    audit_service.log_security_event(
        admin.id, f"account {word}: {user.email}", user.id, commit=False)
    db.session.commit()
    return None


def set_role(admin, user_id, role):
    """Change a user's role (logged as a security event). Returns error or None."""
    if role not in ROLES:
        return "Unknown role."
    user = db.session.get(User, user_id)
    if user is None:
        return "User not found."
    if user.id == admin.id:
        return "You cannot change your own role."
    if user.role == role:
        return None
    old = user.role
    user.role = role
    audit_service.log_security_event(
        admin.id, f"role changed: {user.email} {old} -> {role}", user.id,
        commit=False)
    db.session.commit()
    return None
