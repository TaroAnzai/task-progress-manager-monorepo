# app/routes/reminder_routes.py
from flask import request
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.service_errors import format_error_response
from app.schemas.reminder_schemas import (
     ObjectiveReminderSettingSchema,
     ObjectiveReminderSettingInputSchema,
     ObjectiveReminderSettingUpdateSchema,
     ObjectiveReminderSettingListOutputSchema,
     ObjectiveReminderLogOutputSchema
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
        result, status = reminder_service.list_objective_reminders(objective_id, current_user)
        return result, status
    @login_required
    @reminder_bp.arguments(ObjectiveReminderSettingInputSchema)
    @reminder_bp.response(201, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def post(self, json_data, objective_id: int):
        """create_objective_reminder"""
        result, status = reminder_service.create_objective_reminder(objective_id, json_data, current_user)
        return result, status


# /progress/reminders/<setting_id>
@reminder_bp.route("/reminders/<int:setting_id>")
class ReminderResource(MethodView):
    @login_required
    @reminder_bp.response(200, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def get(self, setting_id: int):
        """get_reminder"""
        result, status = reminder_service.get_reminder(setting_id, current_user)
        return result, status

    @login_required
    @reminder_bp.arguments(ObjectiveReminderSettingUpdateSchema)
    @reminder_bp.response(200, ObjectiveReminderSettingSchema)
    @with_common_error_responses(reminder_bp)
    def patch(self, json_data, setting_id: int):
        """update_reminder"""
        result, status = reminder_service.update_reminder(setting_id, json_data, current_user)
        return result, status
    
    @login_required
    @reminder_bp.response(204)
    @with_common_error_responses(reminder_bp)
    def delete(self, setting_id: int):
        """delete_reminder (204 No Content)"""
        _result, _status = reminder_service.delete_reminder(setting_id, current_user)
        return "", 204
