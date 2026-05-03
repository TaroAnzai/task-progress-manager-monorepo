
from typing import Any, cast
from sqlalchemy.orm import Session
from app.extensions import db
from app.models import User
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
    def post(self, data:dict[str,Any], objective_id:int):
        """進捗追加"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        message = progress_updates_service.add_progress(session, objective_id, data, user)
        return message

    @login_required
    @progress_bp.response(200, ProgressSchema(many=True))
    @with_common_error_responses(progress_bp)
    def get(self, objective_id:int):
        """進捗一覧取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        progress_list = progress_updates_service.get_progress_list(session, objective_id, user)
        return progress_list

@progress_bp.route("/<int:objective_id>/latest-progress")
class LatestProgressResource(MethodView):
    @login_required
    @progress_bp.response(200, ProgressSchema)
    @with_common_error_responses(progress_bp)
    def get(self, objective_id:int):
        """最新進捗取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        progress = progress_updates_service.get_latest_progress(session, objective_id, user)
        return progress

@progress_bp.route("/<int:progress_id>")
class ProgressResource(MethodView):
    @login_required
    @progress_bp.arguments(DeleteQuerySchema, location="query")
    @progress_bp.response(200, MessageSchema)
    @with_common_error_responses(progress_bp)
    def delete(self, args: dict[str, Any], progress_id:int):
        """進捗削除"""
        force = args["force"] 
        session = cast(Session, db.session)
        user = cast(User, current_user)
        message = progress_updates_service.delete_progress(session, progress_id, user, force)
        return message

