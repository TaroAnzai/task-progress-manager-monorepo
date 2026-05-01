# app/services/auth_service.py

from flask import current_app
from flask_login import login_user, logout_user, current_user
from ..models import User
from werkzeug.security import check_password_hash
from ..service_errors import (
    ServiceValidationError,
    ServiceAuthenticationError,
    ServiceNotFoundError,
)

def login_with_email(data):
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ServiceValidationError('email と password は必須です')
    
    email = email.strip().lower()

    user = User.query.filter_by(normalized_email=email).first()
    if not user or not user.check_password(password):
        raise ServiceAuthenticationError('メールアドレスまたはパスワードが無効です')

    login_user(user)
    return {'message': 'ログイン成功', 'user': user}

def login_with_wp_user_id(data):
    wp_user_id = data.get('wp_user_id')
    if not wp_user_id:
        raise ServiceValidationError('wp_user_id は必須です')

    user = User.query.filter_by(wp_user_id=wp_user_id).first()
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    login_user(user)
    return {'message': 'ログイン成功', 'user': user}

def logout_user_session():
    logout_user()
    return {'message': 'ログアウトしました'}

def get_current_user_info():
    if not current_user.is_authenticated:
        return User(
            id=None,
            wp_user_id=None,
            name="",
            email="",
            is_superuser=False,
            organization=None  # organizationは必ずNoneを明示
        )
    return current_user
