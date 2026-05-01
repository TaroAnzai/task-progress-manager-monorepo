from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.service_errors import format_error_response
from flask import jsonify
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
    def post(self, data):
        """オブジェクティブ作成"""
        objective = objectives_service.create_objective(data, current_user)
        return objective

@objectives_bp.route('/<int:objective_id>')
class ObjectiveResource(MethodView):
    @login_required
    @objectives_bp.arguments(ObjectiveUpdateSchema)
    @objectives_bp.response(200, ObjectiveResponseSchema)
    @with_common_error_responses(objectives_bp)
    def put(self, data, objective_id):
        """オブジェクティブ更新"""
        objective = objectives_service.update_objective(objective_id, data, current_user)
        return objective

    @login_required
    @objectives_bp.arguments(DeleteQuerySchema, location="query")
    @objectives_bp.response(200, MessageSchema)
    @with_common_error_responses(objectives_bp)
    def delete(self, args, objective_id):
        """オブジェクティブ削除"""
        force = args["force"] 
        message = objectives_service.delete_objective(objective_id, current_user, force)
        return message

    @login_required
    @objectives_bp.response(200, ObjectiveSchema)
    @with_common_error_responses(objectives_bp)
    def get(self, objective_id):
        """オブジェクティブ詳細取得"""
        objective = objectives_service.get_objective(objective_id, current_user)
        return objective

@objectives_bp.route('/tasks/<int:task_id>')
class TaskObjectivesResource(MethodView):
    @login_required
    @objectives_bp.response(200, ObjectivesListSchema)
    @with_common_error_responses(objectives_bp)
    def get(self, task_id):
        """タスクのオブジェクティブ一覧"""
        objectives = objectives_service.get_objectives_for_task(task_id, current_user)
        return objectives



