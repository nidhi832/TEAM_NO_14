"""Business logic for registration, login and lockout (BL-05, 06, 07, 36, 41).
Pure functions: no Flask and no database imports, so they are easy to unit test.
`user` is any object with the attributes failed_attempts and locked_until.
"""
import re
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

MAX_FAILED_ATTEMPTS = 5          # BL-07
LOCK_MINUTES = 15
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_password(password):
    """BL-41: at least 8 characters with letters and digits. Returns a list of problems."""
    problems = []
    if len(password or "") < 8:
        problems.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Za-z]", password or ""):
        problems.append("Password must contain a letter.")
    if not re.search(r"\d", password or ""):
        problems.append("Password must contain a digit.")
    return problems


def validate_registration(name, email, password):
    """BL-05: returns a list of problems (empty means valid)."""
    problems = []
    if not (name or "").strip():
        problems.append("Name is required.")
    if not EMAIL_RE.match((email or "").strip()):
        problems.append("Enter a valid email address.")
    problems += validate_password(password)
    return problems


def hash_password(password):
    """BL-36: salted hash (werkzeug adds a random salt). Never store the plain password."""
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def is_locked(user, now=None):
    """BL-07: True while the account is inside its lock window."""
    now = now or datetime.utcnow()
    return user.locked_until is not None and user.locked_until > now


def register_failed_login(user, now=None):
    """Call after a wrong password. Locks the account after 5 failures."""
    now = now or datetime.utcnow()
    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
        user.failed_attempts = 0
        return True              # just locked - log a security event (BL-40)
    return False


def register_successful_login(user):
    user.failed_attempts = 0
    user.locked_until = None


def authenticate(user, password, now=None):
    """BL-06: returns (ok, message). Uses one generic message for wrong email or password."""
    generic = "Invalid email or password."
    if user is None:
        return False, generic
    if not getattr(user, "is_active", True):
        return False, "Account is deactivated."          # BL-27
    if is_locked(user, now):
        return False, "Account locked. Try again in 15 minutes."
    if not verify_password(user.password_hash, password):
        register_failed_login(user, now)
        return False, generic
    register_successful_login(user)
    return True, "ok"
