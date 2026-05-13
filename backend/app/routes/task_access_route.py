from typing import Any, cast

from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from app.extensions import db
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.services.task_access_service import get_task_access, get_task_users, update_access_level
from app.schemas import (
    UserWithScopesSchema,
)
from app.schemas import (
    AccessLevelInputSchema,
    MessageSchema,
    TaskAccessListResponseSchema
)
from app.models import User


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
    def put(self, data:dict[str,list[dict[str,Any]]], task_id:int):
        """アクセスレベル更新"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        resp = update_access_level(session, task_id, data, user)
        return resp

@task_access_bp.route('/authorized_users')
class TaskUsersResource(MethodView):
    @login_required
    @task_access_bp.response(200, UserWithScopesSchema(many=True))
    @with_common_error_responses(task_access_bp)
    def get(self, task_id:int):
        """タスクに登録されているユーザー取得"""
        session = cast(Session, db.session)
        resp = get_task_users(session, task_id)
        return resp

@task_access_bp.route('/access_levels')
class TaskAccessUsersResource(MethodView):
    @login_required
    @task_access_bp.response(200, TaskAccessListResponseSchema)
    @with_common_error_responses(task_access_bp)
    def get(self, task_id:int):
        """アクセスサブジェクト一覧"""
        session = cast(Session, db.session)
        resp = get_task_access(session, task_id)
        return resp



