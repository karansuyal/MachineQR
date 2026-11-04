from ..enums import AttachmentKind, FaultCategory, FaultStatus, MachineState
from ..extensions import db
from .base import TimestampMixin, enum_col, utcnow


class FaultReport(TimestampMixin, db.Model):
    __tablename__ = "fault_reports"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(enum_col(FaultCategory), nullable=False, default=FaultCategory.OTHER)
    machine_state = db.Column(enum_col(MachineState), nullable=False)
    error_code = db.Column(db.String(50))
    status = db.Column(
        enum_col(FaultStatus), nullable=False, default=FaultStatus.PENDING, index=True
    )
    reported_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    reported_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime(timezone=True))
    repair_notes = db.Column(db.Text)

    machine = db.relationship("Machine", backref="fault_reports")
    reporter = db.relationship("User", foreign_keys=[reported_by])
    assignee = db.relationship("User", foreign_keys=[assigned_to])
    attachments = db.relationship(
        "FaultAttachment", backref="fault_report", cascade="all, delete-orphan"
    )


class FaultAttachment(db.Model):
    __tablename__ = "fault_attachments"

    id = db.Column(db.Integer, primary_key=True)
    fault_report_id = db.Column(
        db.Integer,
        db.ForeignKey("fault_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind = db.Column(enum_col(AttachmentKind), nullable=False, default=AttachmentKind.REPORT)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
