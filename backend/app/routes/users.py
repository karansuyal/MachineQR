from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user

from ..enums import RoleName
from ..schemas.user import (
    PasswordResetSchema,
    UserCreateSchema,
    UserListQuerySchema,
    UserUpdateSchema,
)
from ..services import user_service
from ..utils.permissions import roles_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("")
@roles_required(RoleName.ADMIN)
def list_users():
    args = UserListQuerySchema().load(request.args.to_dict())
    page = user_service.list_users(
        args["search"], args["role"], args["is_active"], args["page"], args["per_page"]
    )
    return jsonify(
        items=[user_service.serialize_user(u) for u in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
    )


@users_bp.post("")
@roles_required(RoleName.ADMIN)
def create_user():
    data = UserCreateSchema().load(request.get_json(silent=True) or {})
    user = user_service.create_user(data, current_user)
    return jsonify(user=user_service.serialize_user(user)), 201


@users_bp.get("/<int:user_id>")
@roles_required(RoleName.ADMIN)
def get_user(user_id):
    return jsonify(user=user_service.serialize_user(user_service.get_user_or_404(user_id)))


@users_bp.patch("/<int:user_id>")
@roles_required(RoleName.ADMIN)
def update_user(user_id):
    data = UserUpdateSchema().load(request.get_json(silent=True) or {})
    user = user_service.update_user(user_service.get_user_or_404(user_id), data, current_user)
    return jsonify(user=user_service.serialize_user(user))


@users_bp.post("/<int:user_id>/reset-password")
@roles_required(RoleName.ADMIN)
def reset_password(user_id):
    data = PasswordResetSchema().load(request.get_json(silent=True) or {})
    user_service.reset_password(user_service.get_user_or_404(user_id), data["new_password"], current_user)
    return jsonify(message="Password reset")
