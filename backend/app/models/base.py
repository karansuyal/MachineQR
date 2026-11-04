from datetime import datetime, timezone

from ..extensions import db


def utcnow():
    return datetime.now(timezone.utc)


def enum_col(enum_cls):
    return db.Enum(
        enum_cls,
        native_enum=False,
        length=30,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
