from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import current_user, jwt_required

from ..enums import RoleName
from ..errors import ApiError
from ..schemas.machine import (
    AssignmentSchema,
    MachineListQuerySchema,
    MachineSchema,
    StatusSchema,
)
from ..services import machine_service as svc
from ..utils import uploads
from ..utils.permissions import roles_required

machines_bp = Blueprint("machines", __name__, url_prefix="/api/machines")


def _machine_response(machine, status=200):
    return jsonify(machine=svc.serialize_detail(machine, current_user)), status


def _viewable_machine(code):
    machine = svc.get_machine_by_code(code)
    svc.ensure_can_view(current_user, machine)
    return machine


@machines_bp.get("")
@jwt_required()
def list_machines():
    args = MachineListQuerySchema().load(request.args.to_dict())
    page = svc.list_machines(current_user, args)
    return jsonify(
        items=[svc.serialize_summary(m) for m in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
    )


@machines_bp.get("/options")
@jwt_required()
def options():
    return jsonify(svc.machine_options(current_user))


@machines_bp.post("")
@roles_required(RoleName.ADMIN)
def create_machine():
    data = MachineSchema().load(request.get_json(silent=True) or {})
    return _machine_response(svc.create_machine(data, current_user), 201)


@machines_bp.get("/<string:code>")
@jwt_required()
def get_machine(code):
    return _machine_response(_viewable_machine(code))


@machines_bp.patch("/<string:code>")
@roles_required(RoleName.ADMIN)
def update_machine(code):
    machine = svc.get_machine_by_code(code)
    data = MachineSchema(partial=True).load(request.get_json(silent=True) or {})
    return _machine_response(svc.update_machine(machine, data, current_user))


@machines_bp.patch("/<string:code>/status")
@roles_required(RoleName.ADMIN, RoleName.TECHNICIAN)
def update_status(code):
    machine = _viewable_machine(code)
    data = StatusSchema().load(request.get_json(silent=True) or {})
    return _machine_response(svc.set_status(machine, data["status"], current_user))


@machines_bp.post("/<string:code>/deactivate")
@roles_required(RoleName.ADMIN)
def deactivate(code):
    machine = svc.get_machine_by_code(code)
    return _machine_response(svc.set_active(machine, False, current_user))


@machines_bp.post("/<string:code>/reactivate")
@roles_required(RoleName.ADMIN)
def reactivate(code):
    machine = svc.get_machine_by_code(code)
    return _machine_response(svc.set_active(machine, True, current_user))


@machines_bp.put("/<string:code>/assignments")
@roles_required(RoleName.ADMIN)
def update_assignments(code):
    machine = svc.get_machine_by_code(code)
    data = AssignmentSchema().load(request.get_json(silent=True) or {})
    users = svc.replace_assignments(machine, data["user_ids"], current_user)
    return jsonify(assigned_users=users)


@machines_bp.post("/<string:code>/photo")
@roles_required(RoleName.ADMIN)
def upload_photo(code):
    machine = svc.get_machine_by_code(code)
    return _machine_response(svc.set_photo(machine, request.files.get("photo"), current_user))


@machines_bp.delete("/<string:code>/photo")
@roles_required(RoleName.ADMIN)
def delete_photo(code):
    machine = svc.get_machine_by_code(code)
    return _machine_response(svc.remove_photo(machine, current_user))


@machines_bp.get("/<string:code>/photo")
@jwt_required()
def get_photo(code):
    machine = _viewable_machine(code)
    if not machine.photo_path:
        raise ApiError("Machine has no photo", 404)
    response = send_file(uploads.resolve_path(machine.photo_path), mimetype="image/jpeg")
    response.headers["Cache-Control"] = "private, max-age=300"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
