from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.services import task_access_service
from app.schemas import (
    UserWithScopesSchema,
    AccessUserSchema,
    OrgAccessSchema,
    AccessLevelInputSchema,
    MessageSchema,
    ErrorResponseSchema,
)

task_access_bp = Blueprint("TaskAccess", __name__, url_prefix="/tasks/<int:task_id>", description="タスクアクセス")

@task_access_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@task_access_bp.route('/access_levels')
class AccessLevelResource(MethodView):
    @login_required
    @task_access_bp.arguments(AccessLevelInputSchema)
    @task_access_bp.response(200, MessageSchema)
    @with_common_error_responses(task_access_bp)
    def put(self, data, task_id):
        """アクセスレベル更新"""
        resp = task_access_service.update_access_level(task_id, data, current_user)
        return resp

@task_access_bp.route('/authorized_users')
class TaskUsersResource(MethodView):
    @login_required
    @task_access_bp.response(200, UserWithScopesSchema(many=True))
    @with_common_error_responses(task_access_bp)
    def get(self, task_id):
        """タスクに登録されているユーザー取得"""
        resp = task_access_service.get_task_users(task_id)
        return resp

@task_access_bp.route('/access_users')
class TaskAccessUsersResource(MethodView):
    @login_required
    @task_access_bp.response(200, AccessUserSchema(many=True))
    @with_common_error_responses(task_access_bp)
    def get(self, task_id):
        """ユーザーアクセス一覧"""
        resp = task_access_service.get_task_access_users(task_id)
        return resp

@task_access_bp.route('/access_organizations')
class TaskAccessOrganizationsResource(MethodView):
    @login_required
    @task_access_bp.response(200, OrgAccessSchema(many=True))
    @with_common_error_responses(task_access_bp)
    def get(self, task_id):
        """組織アクセス一覧"""
        resp = task_access_service.get_task_access_organizations(task_id)
        return resp

