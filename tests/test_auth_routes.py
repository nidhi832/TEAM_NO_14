import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def client():
    app = create_app({"TESTING": True,
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()


def register(client, email="a@b.com", password="Passw0rdX"):
    return client.post("/register", data={
        "name": "Asha", "email": email, "password": password},
        follow_redirects=True)


def login(client, email="a@b.com", password="Passw0rdX"):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True)


def test_register_creates_account_with_hash(client):
    resp = register(client)
    assert b"Account created" in resp.data
    user = User.query.filter_by(email="a@b.com").first()
    assert user.password_hash != "Passw0rdX"


def test_register_rejects_duplicate_email(client):
    register(client)
    resp = register(client)
    assert b"already exists" in resp.data
    assert User.query.count() == 1


def test_register_rejects_weak_password(client):
    resp = register(client, password="short")
    assert b"at least 8" in resp.data
    assert User.query.count() == 0


def test_login_success_and_logout(client):
    register(client)
    login(client)
    with client.session_transaction() as sess:
        assert sess.get("user_name") == "Asha"
    resp = client.get("/logout", follow_redirects=True)
    assert b"logged out" in resp.data


def test_login_wrong_password_is_generic(client):
    register(client)
    resp = login(client, password="Wrong1234")
    assert b"Invalid email or password." in resp.data
    resp = login(client, email="nobody@b.com")
    assert b"Invalid email or password." in resp.data


def test_account_locks_after_five_failures(client):
    register(client)
    for _ in range(5):
        login(client, password="Wrong1234")
    resp = login(client)  # correct password, but locked now
    assert b"Account locked" in resp.data
