from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required, current_user
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses
from app.services import progress_updates_service
from app.schemas import (
    ProgressInputSchema,
    ProgressSchema,
    MessageSchema,
    DeleteQuerySchema,
)

progress_bp = Blueprint("Progress", __name__, url_prefix = "/updates", description="進捗更新")

@progress_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@progress_bp.route("/<int:objective_id>")
class ProgressListResource(MethodView):
    @login_required
    @progress_bp.arguments(ProgressInputSchema)
    @progress_bp.response(201, MessageSchema)
    @with_common_error_responses(progress_bp)
    def post(self, data, objective_id):
        """進捗追加"""
        message = progress_updates_service.add_progress(objective_id, data, current_user)
        return message

    @login_required
    @progress_bp.response(200, ProgressSchema(many=True))
    @with_common_error_responses(progress_bp)
    def get(self, objective_id):
        """進捗一覧取得"""
        progress_list = progress_updates_service.get_progress_list(objective_id, current_user)
        return progress_list

@progress_bp.route("/<int:objective_id>/latest-progress")
class LatestProgressResource(MethodView):
    @login_required
    @progress_bp.response(200, ProgressSchema)
    @with_common_error_responses(progress_bp)
    def get(self, objective_id):
        """最新進捗取得"""
        progress = progress_updates_service.get_latest_progress(objective_id, current_user)
        return progress

@progress_bp.route("/<int:progress_id>")
class ProgressResource(MethodView):
    @login_required
    @progress_bp.arguments(DeleteQuerySchema, location="query")
    @progress_bp.response(200, MessageSchema)
    @with_common_error_responses(progress_bp)
    def delete(self, args,progress_id):
        """進捗削除"""
        force = args["force"] 
        message = progress_updates_service.delete_progress(progress_id, current_user, force)
        return message

