from flask_smorest import Blueprint
from flask.views import MethodView
from app.service_errors import format_error_response
from flask import jsonify
from flask_login import login_required
from app.services import access_scope_service
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.schemas import (
    AccessScopeSchema,
    AccessScopeInputSchema,
    MessageSchema,
    ErrorResponseSchema,
)

access_scope_bp = Blueprint("AccessScopes", __name__, url_prefix="/access-scopes", description="アクセススコープ管理")


@access_scope_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code

@access_scope_bp.route("/users/<int:user_id>")
class UserAccessScopeResource(MethodView):
    @login_required
    @access_scope_bp.response(200, AccessScopeSchema(many=True))
    @with_common_error_responses(access_scope_bp)
    def get(self, user_id):
        """ユーザーのスコープ一覧"""
        scopes = access_scope_service.get_user_scopes(user_id)
        return scopes

    @login_required
    @access_scope_bp.arguments(AccessScopeInputSchema)
    @access_scope_bp.response(201, MessageSchema)
    @with_common_error_responses(access_scope_bp)
    def post(self, data, user_id):
        """スコープ追加"""
        message = access_scope_service.add_access_scope_to_user(user_id, data)
        return message

@access_scope_bp.route("/<int:scope_id>")
class AccessScopeResource(MethodView):
    @login_required
    @access_scope_bp.response(200, MessageSchema)
    @with_common_error_responses(access_scope_bp)
    def delete(self, scope_id):
        """スコープ削除"""
        message = access_scope_service.delete_access_scope(scope_id)
        return message

