from sqlalchemy.dialects.postgresql import JSONB

from ..enums import Frequency, MaintenanceType
from ..extensions import db
from .base import TimestampMixin, enum_col, utcnow


class MaintenanceSchedule(TimestampMixin, db.Model):
    __tablename__ = "maintenance_schedules"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    frequency = db.Column(enum_col(Frequency), nullable=False)
    checklist = db.Column(JSONB, nullable=False, default=list)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    next_due_date = db.Column(db.Date, nullable=False, index=True)
    last_completed_at = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    machine = db.relationship("Machine", backref="maintenance_schedules")


class MaintenanceRecord(db.Model):
    __tablename__ = "maintenance_records"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, index=True)
    schedule_id = db.Column(
        db.Integer, db.ForeignKey("maintenance_schedules.id", ondelete="SET NULL"), index=True
    )
    fault_report_id = db.Column(
        db.Integer, db.ForeignKey("fault_reports.id", ondelete="SET NULL")
    )
    maintenance_type = db.Column(enum_col(MaintenanceType), nullable=False)
    performed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    performed_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    checklist_result = db.Column(JSONB)
    notes = db.Column(db.Text)

    machine = db.relationship("Machine", backref="maintenance_records")
    technician = db.relationship("User", foreign_keys=[performed_by])
