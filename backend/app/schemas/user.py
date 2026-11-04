from marshmallow import Schema, fields, validate

from ..enums import RoleName
from ..utils.validators import validate_password_strength

ROLE_VALUES = [r.value for r in RoleName]
USERNAME_RULE = validate.Regexp(
    r"^[A-Za-z0-9_.-]+$",
    error="Username may contain letters, numbers, dot, dash and underscore only.",
)


class UserCreateSchema(Schema):
    username = fields.String(
        required=True, validate=[validate.Length(min=3, max=50), USERNAME_RULE]
    )
    email = fields.Email(required=True, validate=validate.Length(max=120))
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    password = fields.String(required=True, validate=validate_password_strength)
    role = fields.String(required=True, validate=validate.OneOf(ROLE_VALUES))


class UserUpdateSchema(Schema):
    email = fields.Email(validate=validate.Length(max=120))
    full_name = fields.String(validate=validate.Length(min=1, max=120))
    role = fields.String(validate=validate.OneOf(ROLE_VALUES))
    is_active = fields.Boolean()


class PasswordResetSchema(Schema):
    new_password = fields.String(required=True, validate=validate_password_strength)


class UserListQuerySchema(Schema):
    search = fields.String(load_default="", validate=validate.Length(max=100))
    role = fields.String(load_default=None, validate=validate.OneOf(ROLE_VALUES))
    is_active = fields.Boolean(load_default=None)
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
