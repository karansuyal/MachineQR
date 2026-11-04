from .auth import auth_bp
from .machines import machines_bp
from .users import users_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(machines_bp)
