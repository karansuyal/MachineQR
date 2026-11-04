from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    current_user,
    decode_token,
    get_jwt,
    jwt_required,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from ..extensions import db
from ..schemas.auth import ChangePasswordSchema, LoginSchema, LogoutSchema
from ..services import auth_service
from ..services.audit import log_action
from ..services.user_service import serialize_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/login")
def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    user = auth_service.authenticate(data["username"], data["password"])
    return jsonify(**auth_service.issue_tokens(user), user=serialize_user(user))


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify(
        access_token=create_access_token(identity=str(current_user.id)),
        user=serialize_user(current_user),
    )


@auth_bp.post("/logout")
@jwt_required()
def logout():
    data = LogoutSchema().load(request.get_json(silent=True) or {})
    auth_service.revoke_token(get_jwt())
    if data["refresh_token"]:
        try:
            refresh_payload = decode_token(data["refresh_token"])
            if refresh_payload["type"] == "refresh" and int(refresh_payload["sub"]) == current_user.id:
                auth_service.revoke_token(refresh_payload)
        except (PyJWTError, JWTExtendedException):
            pass
    log_action("logout", "user", current_user.id, user_id=current_user.id)
    db.session.commit()
    return jsonify(message="Logged out")


@auth_bp.get("/me")
@jwt_required()
def me():
    return jsonify(user=serialize_user(current_user))


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    data = ChangePasswordSchema().load(request.get_json(silent=True) or {})
    auth_service.change_password(current_user, data["current_password"], data["new_password"])
    return jsonify(message="Password updated")
