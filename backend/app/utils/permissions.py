from functools import wraps

from flask_jwt_extended import current_user, verify_jwt_in_request

from ..errors import ApiError


def roles_required(*roles):
    allowed = {getattr(r, "value", r) for r in roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if current_user.role.name not in allowed:
                raise ApiError("You do not have permission to perform this action", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
