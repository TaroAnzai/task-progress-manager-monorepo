#backend\app\util\register_cli.py
import os

import click
from flask.cli import with_appcontext
from app.models import User
from app.extensions import db
from flask import Flask
from werkzeug.security import generate_password_hash

def register_cli(app:Flask):
    app.cli.add_command(create_superuser_command)


@click.command("create-superuser")
@with_appcontext
def create_superuser_command():
    create_superuser()

def create_superuser():


    email = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
    password = os.getenv("SUPERUSER_PASS", "adminpass")
    name = os.getenv("SUPERUSER", "System Admin")

    if not User.query.filter_by(email=email).first():
        user = User()
        user.email = email
        user.password_hash = generate_password_hash(password)
        user.is_superuser = True
        user.name = name
        db.session.add(user)
        db.session.commit()