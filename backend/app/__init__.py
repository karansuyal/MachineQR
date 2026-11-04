from flask import Flask, jsonify

from .cli import register_cli
from .config import Config
from .errors import register_error_handlers
from .extensions import cors, db, jwt, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])

    from . import models  # noqa: F401
    from .routes import register_blueprints
    from .utils.jwt_callbacks import register_jwt_callbacks

    register_jwt_callbacks()
    register_blueprints(app)
    register_error_handlers(app)
    register_cli(app)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
