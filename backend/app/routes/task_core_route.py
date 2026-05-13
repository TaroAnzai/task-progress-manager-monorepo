from typing import Any, cast

from app.schemas.task_access_schemas import AccessSubjectSearchQuerySchema, AccessSubjectSearchResponseSchema
from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from app.extensions import db
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.services import task_core_service
from app.schemas import (
    TaskSchema,
    TaskInputSchema,
    TaskUpdateSchema,
    TaskCreateResponseSchema,
    TaskListResponseSchema,
    OrderSchema,
    MessageSchema,
    StatusSchema,
    DeleteQuerySchema
)
from app.models import User
from app.services.task_access_service import search_access_subjects

task_core_bp = Blueprint("Tasks", __name__, url_prefix="/tasks", description="タスク管理")

@task_core_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@task_core_bp.route("")
class TaskListResource(MethodView):
    @login_required
    @task_core_bp.arguments(TaskInputSchema)
    @task_core_bp.response(201, TaskCreateResponseSchema)
    @with_common_error_responses(task_core_bp)
    def post(self, data:dict[str, Any]):
        """タスク作成"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        resp = task_core_service.create_task(session, data, user)
        return {"message":"タスクを追加しました", "task":resp}

    @login_required
    @task_core_bp.response(200, TaskListResponseSchema)
    @with_common_error_responses(task_core_bp)
    def get(self):
        """タスク一覧"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        resp = task_core_service.get_tasks(session, user)
        return {"tasks": resp}

@task_core_bp.route("/<int:task_id>")
class TaskResource(MethodView):
    @login_required
    @task_core_bp.arguments(TaskUpdateSchema)
    @task_core_bp.response(200, TaskCreateResponseSchema)
    @with_common_error_responses(task_core_bp)
    def put(self, data:dict[str, Any], task_id: int):
        """タスク更新"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        resp = task_core_service.update_task(session, task_id, data, user)
        return {'message':'タスクを更新しました', 'task':resp}

    @login_required
    @task_core_bp.arguments(DeleteQuerySchema, location="query")
    @task_core_bp.response(200, MessageSchema)
    @with_common_error_responses(task_core_bp)
    def delete(self, args:dict[str, bool],task_id: int):
        """タスク削除 (論理・物理)"""
        force = args["force"]
        session = cast(Session, db.session)
        user = cast(User, current_user)
        task_core_service.delete_task(session, task_id, user, force)
        return {'message':'タスクを削除しました'}

    @login_required
    @task_core_bp.response(200, TaskSchema)
    @with_common_error_responses(task_core_bp)
    def get(self, task_id: int):
        """タスク取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        task = task_core_service.get_task_by_id(session, task_id, user)
        return task

@task_core_bp.route("/<int:task_id>/objectives/order")
class ObjectiveOrderResource(MethodView):
    @login_required
    @task_core_bp.arguments(OrderSchema)
    @task_core_bp.response(200, MessageSchema)
    @with_common_error_responses(task_core_bp)
    def post(self, data:dict[str, Any], task_id: int):
        """オブジェクティブ順序更新"""
        session = cast(Session, db.session)
        resp = task_core_service.update_objective_order(session, task_id, data)
        return resp

@task_core_bp.route('/statuses')
class StatusListResource(MethodView):
    @task_core_bp.response(200, StatusSchema(many=True))
    @with_common_error_responses(task_core_bp)
    def get(self):
        """ステータス一覧"""
        result = task_core_service.get_statuses()
        print(result)
        return result

@task_core_bp.route('/access_subjects/search')
class AccessSubjectSearchResource(MethodView):
    @login_required
    @task_core_bp.arguments(AccessSubjectSearchQuerySchema, location="query")
    @task_core_bp.response(200, AccessSubjectSearchResponseSchema)
    @with_common_error_responses(task_core_bp)
    def get(self, args: dict[str,Any]):
        """ユーザー、組織、グループ検索"""
        session = cast(Session, db.session)
        subjects = search_access_subjects(
            session,
            keyword=args["keyword"],
            subject_type=args.get("subject_type"),
            limit=args.get("limit", 20),
        )
        return {
            "subjects": subjects,
        }
