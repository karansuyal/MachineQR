import pytest
from sqlalchemy.exc import IntegrityError

from app.enums import MachineStatus, RoleName
from app.extensions import db
from app.models import Machine, Role, SparePart, User


def test_password_is_hashed(app):
    role = Role(name=RoleName.ADMIN.value)
    db.session.add(role)
    db.session.commit()
    user = User(username="admin1", email="a@x.com", full_name="Admin", role_id=role.id)
    user.set_password("long-secret-pass")
    db.session.add(user)
    db.session.commit()
    assert user.password_hash != "long-secret-pass"
    assert user.check_password("long-secret-pass")
    assert not user.check_password("wrong")


def test_machine_defaults(app):
    machine = Machine(machine_code="M-001", name="Press")
    db.session.add(machine)
    db.session.commit()
    assert machine.status == MachineStatus.STOPPED
    assert machine.is_active is True
    assert machine.qr_version == 1


def test_machine_code_is_unique(app):
    db.session.add(Machine(machine_code="M-001", name="Press"))
    db.session.commit()
    db.session.add(Machine(machine_code="M-001", name="Lathe"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_negative_stock_rejected(app):
    db.session.add(SparePart(name="Fuse", part_number="P-1", quantity=-1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
