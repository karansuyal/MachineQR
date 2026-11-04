from ..enums import StepType
from ..extensions import db
from .base import TimestampMixin, enum_col


class TroubleshootingGuide(TimestampMixin, db.Model):
    __tablename__ = "troubleshooting_guides"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    fault_code = db.Column(db.String(50), index=True)
    symptoms = db.Column(db.Text)
    possible_causes = db.Column(db.Text)
    required_tools = db.Column(db.Text)
    safety_precautions = db.Column(db.Text)
    required_spare_parts = db.Column(db.Text)
    escalation_instructions = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, nullable=False, default=False, index=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = db.Column(db.DateTime(timezone=True))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))

    steps = db.relationship(
        "TroubleshootingStep",
        backref="guide",
        cascade="all, delete-orphan",
        order_by="TroubleshootingStep.step_number",
    )


class TroubleshootingStep(db.Model):
    __tablename__ = "troubleshooting_steps"
    __table_args__ = (db.UniqueConstraint("guide_id", "step_number"),)

    id = db.Column(db.Integer, primary_key=True)
    guide_id = db.Column(
        db.Integer,
        db.ForeignKey("troubleshooting_guides.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number = db.Column(db.Integer, nullable=False)
    step_type = db.Column(enum_col(StepType), nullable=False, default=StepType.INSPECTION)
    instruction = db.Column(db.Text, nullable=False)
    reference_path = db.Column(db.String(255))
