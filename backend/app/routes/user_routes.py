from flask_migrate import current

from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request
from flask_login import login_required, current_user
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.services import user_service
from app.schemas import (
    UserSchema,
    UserSchemaForAdmin,
    UserInputSchema,
    UserUpdateSchema,
    UserCreateResponseSchema,
    MessageSchema,
    UserWithScopesSchema,
    UserQuerySchema,
    DeleteQuerySchema,
)

user_bp = Blueprint("Users", __name__, url_prefix="/users", description="ユーザー管理")

@user_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@user_bp.route("")
class UsersResource(MethodView):
    @login_required
    @user_bp.arguments(UserInputSchema)
    @user_bp.response(201, UserCreateResponseSchema)
    @with_common_error_responses(user_bp)
    def post(self, data):
        """ユーザー作成"""
        result = user_service.create_user(data, current_user)
        return result

    @login_required
    @user_bp.response(200, UserWithScopesSchema(many=True))
    @with_common_error_responses(user_bp)
    def get(self):
        """ユーザー一覧取得"""
        result = user_service.get_users(current_user)
        return result

@user_bp.route("/admin")
class UserResource(MethodView):    
    @login_required
    @user_bp.arguments(UserQuerySchema, location="query")
    @user_bp.response(200, UserSchemaForAdmin(many=True))
    @with_common_error_responses(user_bp)
    def get(self,query_args):
        """ユーザー一覧取得(管理用)"""
        result = user_service.get_user_for_admin(current_user,query_args)
        return result


@user_bp.route("/<int:user_id>")
class UserResource(MethodView):
    @login_required
    @user_bp.response(200, UserWithScopesSchema)
    @with_common_error_responses(user_bp)
    def get(self, user_id):
        """ユーザー取得"""
        result = user_service.get_user_by_id(user_id, current_user)
        return result

    @login_required
    @user_bp.arguments(UserUpdateSchema)
    @user_bp.response(200, UserSchema)
    @with_common_error_responses(user_bp)
    def put(self, data, user_id):
        """ユーザー更新"""
        result = user_service.update_user(user_id, data, current_user)
        return result

    @login_required
    @user_bp.arguments(DeleteQuerySchema, location="query")
    @user_bp.response(200, MessageSchema)
    @with_common_error_responses(user_bp)
    def delete(self, args, user_id):
        """ユーザー削除"""
        force = args["force"] 
        result = user_service.delete_user(user_id, current_user, force)
        return result

@user_bp.route("/email/<string:email>")
class UserByEmailResource(MethodView):
    @login_required
    @user_bp.response(200, UserWithScopesSchema)
    @with_common_error_responses(user_bp)
    def get(self, email):
        """メールアドレスでユーザー取得"""
        result = user_service.get_user_by_email(email, current_user)
        return result

@user_bp.route("/wp/<int:wp_user_id>")
class UserByWPIDResource(MethodView):
    @login_required
    @user_bp.response(200, UserWithScopesSchema)
    @with_common_error_responses(user_bp)
    def get(self, wp_user_id):
        """WordPress IDでユーザー取得"""
        result = user_service.get_user_by_wp_user_id(wp_user_id, current_user)
        return result

@user_bp.route("/by-org-tree/<int:org_id>")
class UsersByOrgTreeResource(MethodView):
    @login_required
    @user_bp.response(200, UserWithScopesSchema(many=True))
    @with_common_error_responses(user_bp)
    def get(self, org_id):
        """組織ツリーでユーザー一覧取得"""
        result = user_service.get_users_by_org_tree(org_id, current_user)
        return result

