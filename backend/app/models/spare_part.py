from ..extensions import db
from .base import TimestampMixin


class SparePart(TimestampMixin, db.Model):
    __tablename__ = "spare_parts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    part_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    manufacturer = db.Column(db.String(150))
    supplier = db.Column(db.String(150))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=0)
    replacement_frequency_days = db.Column(db.Integer)
    specifications = db.Column(db.Text)
    photo_path = db.Column(db.String(255))

    __table_args__ = (
        db.CheckConstraint("quantity >= 0", name="ck_spare_parts_quantity_non_negative"),
        db.CheckConstraint("min_stock_level >= 0", name="ck_spare_parts_min_stock_non_negative"),
    )


class MachineSparePart(db.Model):
    __tablename__ = "machine_spare_parts"
    __table_args__ = (db.UniqueConstraint("machine_id", "spare_part_id"),)

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spare_part_id = db.Column(
        db.Integer, db.ForeignKey("spare_parts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity_required = db.Column(db.Integer, nullable=False, default=1)

    machine = db.relationship("Machine", backref="spare_part_links")
    spare_part = db.relationship("SparePart", backref="machine_links")
