
from flask_smorest import Blueprint
from flask import jsonify
from flask.views import MethodView
from app.decorators import with_common_error_responses
from app.schemas import (
    PasswordResetRequestSchema,
    PasswordResetRequestMessageSchema,
    PasswordResetConfirmSchema,
)
from app.services.auth_password_reset_service import request_password_reset,confirm_password_reset
from app.service_errors import ServiceError
from app.service_errors import format_error_response

password_reset_bp = Blueprint("password_reset", __name__, url_prefix="/auth/password-reset", description="パスワードのリセット用")
@password_reset_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code

@password_reset_bp.route("/request")
class PasswordResetRequestResource(MethodView):
    """
    POST /auth/password-reset/request

    与えられたメールアドレス宛にパスワード再設定リンクを送信します。
    メールの存在有無に関わらず、同じ成功メッセージを返します（情報漏洩防止）。
    """
    @password_reset_bp.arguments(PasswordResetRequestSchema)
    @password_reset_bp.response(200, PasswordResetRequestMessageSchema)
    @with_common_error_responses(password_reset_bp)
    def post(self, args):
        """パスワードリセット要求"""
        res = request_password_reset(args)
        return {"message": res}

@password_reset_bp.route("/confirm")
class PasswordResetConfirmResource(MethodView):
    """
    POST /auth/password-reset/confirm

    受け取った token と new_password を検証し、パスワードを更新します。
    トークン失効・使用済み・期限切れの場合は 400 を返します。
    """
    # @with_common_error_responses(password_reset_bp)
    @password_reset_bp.arguments(PasswordResetConfirmSchema)
    @password_reset_bp.response(200, PasswordResetRequestMessageSchema)
    def post(self, args):
        """パスワードリセット時の変更"""
        res = confirm_password_reset(args)
        return {"message": res}