from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from ..enums import MachineStatus, SpecCategory

STATUS_VALUES = [s.value for s in MachineStatus]
SPEC_CATEGORY_VALUES = [c.value for c in SpecCategory]


def _optional_text(max_length):
    return fields.String(allow_none=True, validate=validate.Length(max=max_length))


class SpecificationSchema(Schema):
    category = fields.String(required=True, validate=validate.OneOf(SPEC_CATEGORY_VALUES))
    spec_key = fields.String(required=True, validate=validate.Length(min=1, max=100))
    spec_value = fields.String(required=True, validate=validate.Length(min=1, max=1000))
    unit = _optional_text(30)


class MachineSchema(Schema):
    name = fields.String(
        required=True,
        validate=[validate.Length(max=150), validate.Regexp(r"\S", error="Name cannot be blank.")],
    )
    category = _optional_text(100)
    department = _optional_text(100)
    production_line = _optional_text(100)
    location = _optional_text(150)
    manufacturer = _optional_text(150)
    model_number = _optional_text(100)
    serial_number = _optional_text(100)
    installation_date = fields.Date(allow_none=True)
    commissioning_date = fields.Date(allow_none=True)
    plc_manufacturer = _optional_text(100)
    plc_model = _optional_text(100)
    hmi_manufacturer = _optional_text(100)
    hmi_model = _optional_text(100)
    operating_instructions = _optional_text(10000)
    technical_notes = _optional_text(10000)
    status = fields.String(validate=validate.OneOf(STATUS_VALUES))
    specifications = fields.List(
        fields.Nested(SpecificationSchema), validate=validate.Length(max=100)
    )

    @validates_schema
    def check_unique_specifications(self, data, **_kwargs):
        seen = set()
        for spec in data.get("specifications", []):
            key = (spec["category"], spec["spec_key"].strip().lower())
            if key in seen:
                raise ValidationError(
                    f"Duplicate specification '{spec['spec_key']}' in the same category.",
                    "specifications",
                )
            seen.add(key)


class MachineListQuerySchema(Schema):
    search = fields.String(load_default="", validate=validate.Length(max=100))
    status = fields.String(load_default=None, validate=validate.OneOf(STATUS_VALUES))
    department = fields.String(load_default=None, validate=validate.Length(max=100))
    category = fields.String(load_default=None, validate=validate.Length(max=100))
    is_active = fields.Boolean(load_default=None)
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))


class StatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(STATUS_VALUES))


class AssignmentSchema(Schema):
    user_ids = fields.List(
        fields.Integer(), required=True, validate=validate.Length(max=200)
    )


class QrSheetQuerySchema(Schema):
    codes = fields.String(load_default="", validate=validate.Length(max=4000))
