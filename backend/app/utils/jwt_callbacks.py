from ..errors import error_response
from ..extensions import db, jwt
from ..models import TokenBlocklist, User


def register_jwt_callbacks():
    @jwt.user_lookup_loader
    def load_user(_header, payload):
        user = db.session.get(User, int(payload["sub"]))
        if user is None or not user.is_active:
            return None
        return user

    @jwt.token_in_blocklist_loader
    def is_revoked(_header, payload):
        return (
            db.session.query(TokenBlocklist.id).filter_by(jti=payload["jti"]).first()
            is not None
        )

    @jwt.user_lookup_error_loader
    def user_lookup_error(_header, _payload):
        return error_response("Account not found or deactivated", 401)

    @jwt.expired_token_loader
    def expired(_header, _payload):
        return error_response("Token has expired", 401)

    @jwt.invalid_token_loader
    def invalid(_reason):
        return error_response("Invalid token", 401)

    @jwt.unauthorized_loader
    def missing(_reason):
        return error_response("Authentication required", 401)

    @jwt.revoked_token_loader
    def revoked(_header, _payload):
        return error_response("Token has been revoked", 401)
