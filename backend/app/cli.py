import click
from marshmallow import ValidationError

from .enums import RoleName
from .extensions import db
from .models import Role, User
from .utils.validators import validate_password_strength


def register_cli(app):
    @app.cli.command("seed-roles")
    def seed_roles():
        existing = {name for (name,) in db.session.query(Role.name).all()}
        missing = [r.value for r in RoleName if r.value not in existing]
        db.session.add_all(Role(name=name) for name in missing)
        db.session.commit()
        click.echo(f"Roles added: {missing or 'none'}")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--full-name", prompt=True)
    @click.password_option()
    def create_admin(username, email, full_name, password):
        role = Role.query.filter_by(name=RoleName.ADMIN.value).first()
        if role is None:
            raise click.ClickException("Run seed-roles first.")
        try:
            validate_password_strength(password)
        except ValidationError as err:
            raise click.ClickException(err.messages[0])
        user = User(
            username=username.strip().lower(),
            email=email.strip().lower(),
            full_name=full_name.strip(),
            role_id=role.id,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin '{user.username}' created.")
