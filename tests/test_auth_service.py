from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services import auth_service as a


def make_user(pw="abc12345"):
    return SimpleNamespace(password_hash=a.hash_password(pw), failed_attempts=0,
                           locked_until=None, is_active=True)


def test_password_policy():
    assert a.validate_password("abc12345") == []
    assert a.validate_password("abcdefgh")      # no digit
    assert a.validate_password("12345678")      # no letter
    assert a.validate_password("a1")            # too short


def test_registration_validation():
    assert a.validate_registration("Sri", "s@x.com", "abc12345") == []
    assert a.validate_registration("", "bad", "x")


def test_hash_is_salted_and_not_plain():
    h1, h2 = a.hash_password("abc12345"), a.hash_password("abc12345")
    assert h1 != h2 and "abc12345" not in h1
    assert a.verify_password(h1, "abc12345") and not a.verify_password(h1, "wrong")


def test_login_ok_and_generic_error():
    u = make_user()
    assert a.authenticate(u, "abc12345")[0]
    assert a.authenticate(u, "nope") == (False, "Invalid email or password.")
    assert a.authenticate(None, "x") == (False, "Invalid email or password.")


def test_lock_after_five_failures_for_15_minutes():
    u, t = make_user(), datetime(2026, 10, 23, 12, 0)
    for _ in range(5):
        a.authenticate(u, "wrong", t)
    ok, msg = a.authenticate(u, "abc12345", t)      # 6th attempt, even with right password
    assert not ok and "locked" in msg.lower()
    assert a.authenticate(u, "abc12345", t + timedelta(minutes=16))[0]


def test_deactivated_user_cannot_login():
    u = make_user(); u.is_active = False
    assert not a.authenticate(u, "abc12345")[0]
