from marshmallow import ValidationError


def validate_password_strength(value):
    if len(value) < 10:
        raise ValidationError("Password must be at least 10 characters.")
    if len(value) > 128:
        raise ValidationError("Password must be at most 128 characters.")
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValidationError("Password must contain both letters and numbers.")
