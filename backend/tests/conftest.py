import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402
from app.enums import RoleName  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Machine, MachineAssignment, Role, User  # noqa: E402

from .constants import PASSWORD  # noqa: E402


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ["TEST_DATABASE_URL"]


@pytest.fixture()
def app(tmp_path):
    app = create_app(TestingConfig)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def users(app):
    roles = {}
    for name in RoleName:
        role = Role(name=name.value)
        db.session.add(role)
        roles[name.value] = role
    db.session.flush()
    created = {}
    for name in RoleName:
        user = User(
            username=name.value,
            email=f"{name.value}@example.com",
            full_name=name.value.title(),
            role_id=roles[name.value].id,
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        created[name.value] = user
    db.session.commit()
    return created


@pytest.fixture()
def login(client):
    def _login(username, password=PASSWORD):
        return client.post("/api/auth/login", json={"username": username, "password": password})

    return _login


@pytest.fixture()
def auth(login):
    def _auth(username):
        token = login(username).get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth


@pytest.fixture()
def make_machine(app):
    def _make(code="M-001", name="Press 1", **kwargs):
        machine = Machine(machine_code=code, name=name, **kwargs)
        db.session.add(machine)
        db.session.commit()
        return machine

    return _make


@pytest.fixture()
def assign(app):
    def _assign(machine, *assignees):
        for person in assignees:
            db.session.add(MachineAssignment(machine_id=machine.id, user_id=person.id))
        db.session.commit()

    return _assign
