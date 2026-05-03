from typing import Any, cast

from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from app.models import User
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.service_errors import format_error_response
from flask import jsonify
from app.extensions import db
from app.services import objectives_service
from app.schemas import (
    ObjectiveSchema,
    ObjectiveInputSchema,
    ObjectiveUpdateSchema,
    ObjectiveResponseSchema,
    ObjectivesListSchema,
    MessageSchema,
    DeleteQuerySchema,
)
from sqlalchemy.orm import Session

objectives_bp = Blueprint("Objectives", __name__, url_prefix="/objectives", description="オブジェクティブ管理")

@objectives_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@objectives_bp.route('')
class ObjectiveListResource(MethodView):
    @login_required
    @objectives_bp.arguments(ObjectiveInputSchema)
    @objectives_bp.response(201, ObjectiveResponseSchema)
    @with_common_error_responses(objectives_bp)
    def post(self, data: dict[str, Any]):
        """オブジェクティブ作成"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        objective = objectives_service.create_objective(session, data, user)
        return objective

@objectives_bp.route('/<int:objective_id>')
class ObjectiveResource(MethodView):
    @login_required
    @objectives_bp.arguments(ObjectiveUpdateSchema)
    @objectives_bp.response(200, ObjectiveResponseSchema)
    @with_common_error_responses(objectives_bp)
    def put(self, data: dict[str, Any], objective_id: int):
        """オブジェクティブ更新"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        objective = objectives_service.update_objective(session, objective_id, data, user)
        return objective

    @login_required
    @objectives_bp.arguments(DeleteQuerySchema, location="query")
    @objectives_bp.response(200, MessageSchema)
    @with_common_error_responses(objectives_bp)
    def delete(self, args: dict[str, Any], objective_id: int):
        """オブジェクティブ削除"""
        force = args["force"] 
        session = cast(Session, db.session)
        user = cast(User, current_user)
        message = objectives_service.delete_objective(session, objective_id, user, force)
        return message

    @login_required
    @objectives_bp.response(200, ObjectiveSchema)
    @with_common_error_responses(objectives_bp)
    def get(self, objective_id: int):
        """オブジェクティブ詳細取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        objective = objectives_service.get_objective(session, objective_id, user)
        return objective

@objectives_bp.route('/tasks/<int:task_id>')
class TaskObjectivesResource(MethodView):
    @login_required
    @objectives_bp.response(200, ObjectivesListSchema)
    @with_common_error_responses(objectives_bp)
    def get(self, task_id: int):
        """タスクのオブジェクティブ一覧"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        objectives = objectives_service.get_objectives_for_task(session, task_id, user)
        return objectives



