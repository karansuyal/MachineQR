from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..errors import ApiError
from ..extensions import db
from ..models import TokenBlocklist, User
from ..models.base import utcnow
from .audit import log_action

_DUMMY_HASH = generate_password_hash("timing-equalizer-password")
_INVALID_CREDENTIALS = "Invalid username or password"


def authenticate(username, password):
    username = username.strip().lower()
    user = User.query.filter_by(username=username).first()

    if user is None:
        check_password_hash(_DUMMY_HASH, password)
        log_action("login_failed", details={"username": username[:50], "reason": "unknown_user"})
        db.session.commit()
        raise ApiError(_INVALID_CREDENTIALS, 401)

    now = utcnow()
    if user.locked_until and user.locked_until > now:
        log_action("login_blocked", "user", user.id, {"reason": "locked"}, user_id=user.id)
        db.session.commit()
        raise ApiError("Account is temporarily locked. Try again later.", 423)

    if not user.check_password(password):
        user.failed_login_count += 1
        log_action("login_failed", "user", user.id, {"reason": "bad_password"}, user_id=user.id)
        if user.failed_login_count >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
            minutes = current_app.config["LOGIN_LOCKOUT_MINUTES"]
            user.locked_until = now + timedelta(minutes=minutes)
            user.failed_login_count = 0
            log_action("account_locked", "user", user.id, {"minutes": minutes}, user_id=user.id)
        db.session.commit()
        raise ApiError(_INVALID_CREDENTIALS, 401)

    if not user.is_active:
        log_action("login_blocked", "user", user.id, {"reason": "inactive"}, user_id=user.id)
        db.session.commit()
        raise ApiError("Your account is deactivated. Contact an administrator.", 403)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    log_action("login_success", "user", user.id, user_id=user.id)
    db.session.commit()
    return user


def issue_tokens(user):
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
    }


def revoke_token(payload):
    jti = payload["jti"]
    if db.session.query(TokenBlocklist.id).filter_by(jti=jti).first():
        return
    db.session.add(
        TokenBlocklist(
            jti=jti,
            token_type=payload["type"],
            user_id=int(payload["sub"]),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    )


def change_password(user, current_password, new_password):
    if not user.check_password(current_password):
        raise ApiError("Current password is incorrect", 400)
    user.set_password(new_password)
    log_action("password_changed", "user", user.id, user_id=user.id)
    db.session.commit()
