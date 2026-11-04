from sqlalchemy import Integer, cast, func
from sqlalchemy.exc import IntegrityError

from ..enums import MachineStatus, RoleName, SpecCategory
from ..errors import ApiError
from ..extensions import db
from ..models import Machine, MachineAssignment, MachineSpecification, Role, User
from ..models.base import utcnow
from ..utils import uploads
from .audit import log_action

EDITABLE_FIELDS = (
    "name", "category", "department", "production_line", "location", "manufacturer",
    "model_number", "serial_number", "installation_date", "commissioning_date",
    "plc_manufacturer", "plc_model", "hmi_manufacturer", "hmi_model",
    "operating_instructions", "technical_notes",
)
CODE_PATTERN = r"^M-[0-9]+$"


def _is_admin(user):
    return user.role.name == RoleName.ADMIN.value


def _iso(value):
    return value.isoformat() if value else None


def _enum_value(value):
    return getattr(value, "value", value)


def serialize_summary(machine):
    return {
        "id": machine.id,
        "machine_code": machine.machine_code,
        "name": machine.name,
        "category": machine.category,
        "department": machine.department,
        "production_line": machine.production_line,
        "location": machine.location,
        "manufacturer": machine.manufacturer,
        "model_number": machine.model_number,
        "status": _enum_value(machine.status),
        "is_active": machine.is_active,
        "has_photo": bool(machine.photo_path),
        "updated_at": _iso(machine.updated_at),
    }


def serialize_assigned_users(machine):
    rows = (
        db.session.query(User)
        .join(MachineAssignment, MachineAssignment.user_id == User.id)
        .filter(MachineAssignment.machine_id == machine.id)
        .order_by(User.full_name)
        .all()
    )
    return [
        {"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role.name}
        for u in rows
    ]


def _group_specifications(machine):
    order = {c.value: i for i, c in enumerate(SpecCategory)}
    ordered = sorted(
        machine.specifications,
        key=lambda s: (order[_enum_value(s.category)], s.spec_key.lower()),
    )
    groups = {}
    for spec in ordered:
        groups.setdefault(_enum_value(spec.category), []).append(
            {"id": spec.id, "spec_key": spec.spec_key, "spec_value": spec.spec_value, "unit": spec.unit}
        )
    return [{"category": category, "items": items} for category, items in groups.items()]


def serialize_detail(machine, user):
    full_access = user.role.name != RoleName.OPERATOR.value
    data = serialize_summary(machine)
    data.update(
        serial_number=machine.serial_number,
        installation_date=_iso(machine.installation_date),
        commissioning_date=_iso(machine.commissioning_date),
        operating_instructions=machine.operating_instructions,
        created_at=_iso(machine.created_at),
        access_level="full" if full_access else "basic",
    )
    if full_access:
        data.update(
            plc_manufacturer=machine.plc_manufacturer,
            plc_model=machine.plc_model,
            hmi_manufacturer=machine.hmi_manufacturer,
            hmi_model=machine.hmi_model,
            technical_notes=machine.technical_notes,
            specifications=_group_specifications(machine),
        )
    if _is_admin(user):
        data["assigned_users"] = serialize_assigned_users(machine)
    return data


def get_machine_by_code(code):
    machine = Machine.query.filter_by(machine_code=code.strip().upper()).first()
    if machine is None:
        raise ApiError("Machine not found", 404)
    return machine


def ensure_can_view(user, machine):
    if _is_admin(user):
        return
    if not machine.is_active:
        raise ApiError("Machine not found", 404)
    assigned = (
        db.session.query(MachineAssignment.id)
        .filter_by(machine_id=machine.id, user_id=user.id)
        .first()
    )
    if assigned is None:
        raise ApiError("You are not assigned to this machine. Contact an administrator.", 403)


def _visible_query(user):
    query = Machine.query
    if _is_admin(user):
        return query
    return query.join(MachineAssignment, MachineAssignment.machine_id == Machine.id).filter(
        MachineAssignment.user_id == user.id, Machine.is_active.is_(True)
    )


def list_machines(user, args):
    query = _visible_query(user)
    if _is_admin(user) and args["is_active"] is not None:
        query = query.filter(Machine.is_active == args["is_active"])
    if args["search"]:
        like = f"%{args['search']}%"
        query = query.filter(
            db.or_(
                Machine.machine_code.ilike(like),
                Machine.name.ilike(like),
                Machine.manufacturer.ilike(like),
                Machine.model_number.ilike(like),
            )
        )
    if args["status"]:
        query = query.filter(Machine.status == MachineStatus(args["status"]))
    if args["department"]:
        query = query.filter(Machine.department == args["department"])
    if args["category"]:
        query = query.filter(Machine.category == args["category"])
    return query.order_by(func.length(Machine.machine_code), Machine.machine_code).paginate(
        page=args["page"], per_page=args["per_page"], error_out=False
    )


def machine_options(user):
    rows = _visible_query(user).with_entities(Machine.department, Machine.category).all()
    return {
        "departments": sorted({r[0] for r in rows if r[0]}),
        "categories": sorted({r[1] for r in rows if r[1]}),
    }


def _clean(data):
    cleaned = {}
    for field in EDITABLE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if isinstance(value, str):
            value = value.strip() or None
        cleaned[field] = value
    if "name" in cleaned and cleaned["name"] is None:
        raise ApiError("Machine name cannot be blank", 400)
    return cleaned


def _validate_dates(installation, commissioning):
    if installation and commissioning and commissioning < installation:
        raise ApiError("Commissioning date cannot be before installation date", 400)


def _next_machine_code():
    highest = (
        db.session.query(func.max(cast(func.substr(Machine.machine_code, 3), Integer)))
        .filter(Machine.machine_code.op("~")(CODE_PATTERN))
        .scalar()
    )
    return f"M-{(highest or 0) + 1:03d}"


def _replace_specifications(machine, specs):
    machine.specifications.clear()
    db.session.flush()
    for spec in specs:
        machine.specifications.append(
            MachineSpecification(
                category=SpecCategory(spec["category"]),
                spec_key=spec["spec_key"].strip(),
                spec_value=spec["spec_value"].strip(),
                unit=(spec.get("unit") or "").strip() or None,
                is_custom=spec["category"] == SpecCategory.CUSTOM.value,
            )
        )
    db.session.flush()


def create_machine(data, actor):
    specs = data.pop("specifications", None)
    status = data.pop("status", None)
    cleaned = _clean(data)
    _validate_dates(cleaned.get("installation_date"), cleaned.get("commissioning_date"))

    for _attempt in range(3):
        machine = Machine(machine_code=_next_machine_code(), **cleaned)
        if status:
            machine.status = MachineStatus(status)
        try:
            with db.session.begin_nested():
                db.session.add(machine)
                db.session.flush()
            break
        except IntegrityError:
            continue
    else:
        raise ApiError("Could not allocate a machine ID. Please try again.", 409)

    if specs:
        _replace_specifications(machine, specs)
    log_action(
        "machine_created", "machine", machine.id,
        {"machine_code": machine.machine_code, "name": machine.name}, user_id=actor.id,
    )
    db.session.commit()
    return machine


def update_machine(machine, data, actor):
    specs = data.pop("specifications", None)
    status = data.pop("status", None)
    cleaned = _clean(data)
    _validate_dates(
        cleaned.get("installation_date", machine.installation_date),
        cleaned.get("commissioning_date", machine.commissioning_date),
    )

    changed = []
    for field, value in cleaned.items():
        if getattr(machine, field) != value:
            setattr(machine, field, value)
            changed.append(field)
    if status and _enum_value(machine.status) != status:
        _apply_status(machine, status, actor)
    if specs is not None:
        _replace_specifications(machine, specs)
        machine.updated_at = utcnow()
        changed.append("specifications")
    if changed:
        log_action(
            "machine_updated", "machine", machine.id,
            {"machine_code": machine.machine_code, "fields": changed}, user_id=actor.id,
        )
    db.session.commit()
    return machine


def _apply_status(machine, status, actor):
    previous = _enum_value(machine.status)
    machine.status = MachineStatus(status)
    log_action(
        "machine_status_changed", "machine", machine.id,
        {"machine_code": machine.machine_code, "from": previous, "to": status}, user_id=actor.id,
    )


def set_status(machine, status, actor):
    if not machine.is_active:
        raise ApiError("Machine is deactivated", 400)
    if _enum_value(machine.status) != status:
        _apply_status(machine, status, actor)
        db.session.commit()
    return machine


def set_active(machine, active, actor):
    if machine.is_active != active:
        machine.is_active = active
        log_action(
            "machine_reactivated" if active else "machine_deactivated",
            "machine", machine.id, {"machine_code": machine.machine_code}, user_id=actor.id,
        )
        db.session.commit()
    return machine


def replace_assignments(machine, user_ids, actor):
    wanted = set(user_ids)
    users = User.query.filter(User.id.in_(wanted)).all() if wanted else []
    if len(users) != len(wanted):
        raise ApiError("One or more users do not exist", 400)
    for user in users:
        if not user.is_active:
            raise ApiError(f"User '{user.username}' is deactivated", 400)
        if user.role.name == RoleName.ADMIN.value:
            raise ApiError("Admins already have access to every machine", 400)

    existing = {
        a.user_id: a for a in MachineAssignment.query.filter_by(machine_id=machine.id).all()
    }
    removed = sorted(set(existing) - wanted)
    added = sorted(wanted - set(existing))
    for user_id in removed:
        db.session.delete(existing[user_id])
    for user_id in added:
        db.session.add(MachineAssignment(machine_id=machine.id, user_id=user_id))
    if added or removed:
        log_action(
            "machine_assignments_updated", "machine", machine.id,
            {"machine_code": machine.machine_code, "added": added, "removed": removed},
            user_id=actor.id,
        )
    db.session.commit()
    return serialize_assigned_users(machine)


def set_photo(machine, file_storage, actor):
    new_path = uploads.save_image(file_storage, "machine_photos")
    old_path = machine.photo_path
    machine.photo_path = new_path
    machine.updated_at = utcnow()
    log_action(
        "machine_photo_updated", "machine", machine.id,
        {"machine_code": machine.machine_code}, user_id=actor.id,
    )
    db.session.commit()
    uploads.delete_file(old_path)
    return machine


def remove_photo(machine, actor):
    old_path = machine.photo_path
    if old_path:
        machine.photo_path = None
        machine.updated_at = utcnow()
        log_action(
            "machine_photo_removed", "machine", machine.id,
            {"machine_code": machine.machine_code}, user_id=actor.id,
        )
        db.session.commit()
        uploads.delete_file(old_path)
    return machine
