from marshmallow import Schema, fields, validate

from ..utils.validators import validate_password_strength


class LoginSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=1, max=50))
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))


class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True, validate=validate.Length(min=1, max=128))
    new_password = fields.String(required=True, validate=validate_password_strength)


class LogoutSchema(Schema):
    refresh_token = fields.String(load_default=None)
