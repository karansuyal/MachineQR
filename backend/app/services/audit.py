from flask import has_request_context, request

from ..extensions import db
from ..models import AuditLog


def log_action(action, entity_type=None, entity_id=None, details=None, user_id=None):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr if has_request_context() else None,
    )
    db.session.add(entry)
    return entry
