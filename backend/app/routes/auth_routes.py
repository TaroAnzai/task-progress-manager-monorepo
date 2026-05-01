from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import jsonify
from app.service_errors import format_error_response
from flask_login import login_required
from app.services import auth_service
from app.schemas import (
    LoginSchema,
    WPLoginSchema,
    UserSchema,
    UserWithScopesSchema,
    UserCreateResponseSchema,
    LoginResponseSchema,
    MessageSchema,
    ErrorResponseSchema,
)
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses

auth_bp = Blueprint("Auth", __name__, url_prefix="/sessions", description="認証")

@auth_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@auth_bp.route("")
class LoginResource(MethodView):
    @auth_bp.arguments(LoginSchema)
    @auth_bp.response(200, LoginResponseSchema)
    @with_common_error_responses(auth_bp)
    def post(self, data):
        """メールでログイン"""
        user_info = auth_service.login_with_email(data)
        return user_info

@auth_bp.route("/by-id")
class LoginByIDResource(MethodView):
    @auth_bp.arguments(WPLoginSchema)
    @auth_bp.response(200, LoginResponseSchema)
    @with_common_error_responses(auth_bp)
    def post(self, data):
        """WP IDでログイン"""
        user_info = auth_service.login_with_wp_user_id(data)
        return user_info

@auth_bp.route("/current")
class LogoutResource(MethodView):
    @login_required
    @auth_bp.response(200, MessageSchema)
    @with_common_error_responses(auth_bp)
    def delete(self):
        """ログアウト"""
        message = auth_service.logout_user_session()
        return message

@auth_bp.route("/current")
class CurrentUserResource(MethodView):
    @auth_bp.response(200, UserWithScopesSchema)
    @with_common_error_responses(auth_bp)
    def get(self):
        """現在のユーザー取得"""
        user = auth_service.get_current_user_info()
        return user

