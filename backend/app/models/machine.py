from ..enums import DocumentType, MachineStatus, SpecCategory
from ..extensions import db
from .base import TimestampMixin, enum_col, utcnow


class Machine(TimestampMixin, db.Model):
    __tablename__ = "machines"

    id = db.Column(db.Integer, primary_key=True)
    machine_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))
    department = db.Column(db.String(100), index=True)
    production_line = db.Column(db.String(100))
    location = db.Column(db.String(150))
    manufacturer = db.Column(db.String(150))
    model_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    installation_date = db.Column(db.Date)
    commissioning_date = db.Column(db.Date)
    photo_path = db.Column(db.String(255))
    status = db.Column(
        enum_col(MachineStatus), nullable=False, default=MachineStatus.STOPPED, index=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    plc_manufacturer = db.Column(db.String(100))
    plc_model = db.Column(db.String(100))
    hmi_manufacturer = db.Column(db.String(100))
    hmi_model = db.Column(db.String(100))
    operating_instructions = db.Column(db.Text)
    technical_notes = db.Column(db.Text)
    qr_version = db.Column(db.Integer, nullable=False, default=1)
    qr_generated_at = db.Column(db.DateTime(timezone=True))

    specifications = db.relationship(
        "MachineSpecification", backref="machine", cascade="all, delete-orphan"
    )
    documents = db.relationship(
        "MachineDocument", backref="machine", cascade="all, delete-orphan"
    )


class MachineSpecification(TimestampMixin, db.Model):
    __tablename__ = "machine_specifications"
    __table_args__ = (db.UniqueConstraint("machine_id", "category", "spec_key"),)

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category = db.Column(enum_col(SpecCategory), nullable=False)
    spec_key = db.Column(db.String(100), nullable=False)
    spec_value = db.Column(db.Text, nullable=False)
    unit = db.Column(db.String(30))
    is_custom = db.Column(db.Boolean, nullable=False, default=False)


class MachineDocument(db.Model):
    __tablename__ = "machine_documents"

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    doc_type = db.Column(enum_col(DocumentType), nullable=False, default=DocumentType.OTHER)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class MachineAssignment(db.Model):
    __tablename__ = "machine_assignments"
    __table_args__ = (db.UniqueConstraint("machine_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
