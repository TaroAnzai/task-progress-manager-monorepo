# app/routes/reminder_routes.py
from typing import Any, cast
from sqlalchemy.orm import Session
from app.extensions import db

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.models import User
from app.service_errors import format_error_response
from app.schemas.reminder_schemas import (
     ObjectiveReminderSettingSchema,
     ObjectiveReminderSettingInputSchema,
     ObjectiveReminderSettingUpdateSchema,
     ObjectiveReminderSettingListOutputSchema,
)
from app.services import reminder_service  # 命名ルールに従う
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses

reminder_bp = Blueprint(
    "reminders",
    __name__,
    url_prefix="/",
    description="Objective reminder settings",
)
@reminder_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code

# /progress/objectives/<objective_id>/reminders
@reminder_bp.route("/objectives/<int:objective_id>/reminders")
class ObjectiveRemindersResource(MethodView):
    @login_required
    @reminder_bp.response(200, ObjectiveReminderSettingListOutputSchema)
    @with_common_error_responses(reminder_bp)
    def get(self, objective_id: int):
        """list_objective_reminders"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        result, status = reminder_service.list_objective_reminders(session, objective_id, user)
        return result, status
    
    @login_required
    @reminder_bp.arguments(ObjectiveReminderSettingInputSchema)
    @reminder_bp.response(201, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def post(self, json_data:dict[str, Any], objective_id: int):
        """create_objective_reminder"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        result, status = reminder_service.create_objective_reminder(session, objective_id, json_data, user)
        return result, status


# /progress/reminders/<setting_id>
@reminder_bp.route("/reminders/<int:setting_id>")
class ReminderResource(MethodView):
    @login_required
    @reminder_bp.response(200, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def get(self, setting_id: int):
        """get_reminder"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        result, status = reminder_service.get_reminder(session, setting_id, user)
        return result, status

    @login_required
    @reminder_bp.arguments(ObjectiveReminderSettingUpdateSchema)
    @reminder_bp.response(200, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def patch(self, json_data:dict[str, Any], setting_id: int):
        """update_reminder"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        result, status = reminder_service.update_reminder(session, setting_id, json_data, user)
        return result, status
    
    @login_required
    @reminder_bp.response(204)
    @with_common_error_responses(reminder_bp)
    def delete(self, setting_id: int):
        """delete_reminder (204 No Content)"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        _result, _status = reminder_service.delete_reminder(session, setting_id, user)
        return "", 204
