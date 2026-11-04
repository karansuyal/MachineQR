import enum


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    OPERATOR = "operator"


class MachineStatus(str, enum.Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    UNDER_MAINTENANCE = "under_maintenance"


class SpecCategory(str, enum.Enum):
    MOTOR = "motor"
    SENSOR = "sensor"
    ELECTRICAL = "electrical"
    PNEUMATIC = "pneumatic"
    HYDRAULIC = "hydraulic"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


class DocumentType(str, enum.Enum):
    MANUAL = "manual"
    DRAWING = "drawing"
    IMAGE = "image"
    OTHER = "other"


class StepType(str, enum.Enum):
    INSPECTION = "inspection"
    CORRECTIVE = "corrective"


class FaultCategory(str, enum.Enum):
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PNEUMATIC = "pneumatic"
    HYDRAULIC = "hydraulic"
    SOFTWARE = "software"
    SAFETY = "safety"
    OTHER = "other"


class FaultStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MachineState(str, enum.Enum):
    RUNNING = "running"
    STOPPED = "stopped"


class AttachmentKind(str, enum.Enum):
    REPORT = "report"
    REPAIR = "repair"


class Frequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
