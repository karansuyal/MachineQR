from sqlalchemy.exc import IntegrityError

from ..errors import ApiError
from ..extensions import db
from ..models import Role, User
from .audit import log_action


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
    }


def get_role(name):
    role = Role.query.filter_by(name=name).first()
    if role is None:
        raise ApiError("Role is not configured. Run seed-roles.", 500)
    return role


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("User not found", 404)
    return user


def _ensure_unique(username=None, email=None, exclude_id=None):
    if username is not None:
        query = User.query.filter(User.username == username)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        if query.first():
            raise ApiError("Username is already taken", 409)
    if email is not None:
        query = User.query.filter(User.email == email)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        if query.first():
            raise ApiError("Email is already in use", 409)


def list_users(search, role, is_active, page, per_page):
    query = User.query.join(Role)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(like),
                User.full_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if role:
        query = query.filter(Role.name == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.full_name).paginate(
        page=page, per_page=per_page, error_out=False
    )


def create_user(data, actor):
    username = data["username"].strip().lower()
    email = data["email"].strip().lower()
    _ensure_unique(username=username, email=email)
    user = User(
        username=username,
        email=email,
        full_name=data["full_name"].strip(),
        role_id=get_role(data["role"]).id,
    )
    user.set_password(data["password"])
    db.session.add(user)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("Username or email already exists", 409)
    log_action(
        "user_created", "user", user.id,
        {"username": username, "role": data["role"]}, user_id=actor.id,
    )
    db.session.commit()
    return user


def update_user(user, data, actor):
    if user.id == actor.id:
        if data.get("is_active") is False:
            raise ApiError("You cannot deactivate your own account", 400)
        if "role" in data and data["role"] != user.role.name:
            raise ApiError("You cannot change your own role", 400)

    changes = {}
    if "email" in data:
        email = data["email"].strip().lower()
        _ensure_unique(email=email, exclude_id=user.id)
        if email != user.email:
            changes["email"] = email
            user.email = email
    if "full_name" in data and data["full_name"].strip() != user.full_name:
        user.full_name = data["full_name"].strip()
        changes["full_name"] = user.full_name
    if "role" in data and data["role"] != user.role.name:
        user.role_id = get_role(data["role"]).id
        changes["role"] = data["role"]
    if "is_active" in data and data["is_active"] != user.is_active:
        user.is_active = data["is_active"]
        changes["is_active"] = data["is_active"]

    if changes:
        log_action("user_updated", "user", user.id, changes, user_id=actor.id)
    db.session.commit()
    db.session.refresh(user)
    return user


def reset_password(user, new_password, actor):
    user.set_password(new_password)
    user.failed_login_count = 0
    user.locked_until = None
    log_action("password_reset_by_admin", "user", user.id, user_id=actor.id)
    db.session.commit()
