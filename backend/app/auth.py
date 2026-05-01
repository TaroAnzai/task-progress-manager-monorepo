# app/routes/auth_routes.py
from flask import Blueprint, jsonify
from app.extensions import login_manager
from app import db
from app.models import User
from app.service_errors import (
    ServiceValidationError,
    ServiceAuthenticationError,
    ServiceNotFoundError,
)

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    raise ServiceAuthenticationError('ログインが必要です')
