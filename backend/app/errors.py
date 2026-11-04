from flask import current_app, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from .extensions import db


class ApiError(Exception):
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def error_response(message, status_code, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status_code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return error_response(err.message, err.status_code, err.details)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return error_response("Validation failed", 400, err.messages)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return error_response(err.description, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        current_app.logger.exception("Unhandled error")
        return error_response("Internal server error", 500)
