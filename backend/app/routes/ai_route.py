from app.service_errors import format_error_response
from flask import jsonify
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_login import login_required
from app.services import ai_service
from app.schemas import (
    AISuggestInputSchema,
    JobIdSchema,
    AIResultSchema,
    ErrorResponseSchema,
)
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses

ai_bp = Blueprint("AI", __name__, url_prefix="/ai", description="AI 提案")

@ai_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code


@ai_bp.route("/suggest")
class AISuggestResource(MethodView):
    @login_required
    @ai_bp.arguments(AISuggestInputSchema)
    @ai_bp.response(202, JobIdSchema)
    @with_common_error_responses(ai_bp)
    def post(self, data):
        """AI提案実行"""
        job = ai_service.enqueue_ai_task(data)
        return job

@ai_bp.route("/result/<job_id>")
class AIResultResource(MethodView):
    @login_required
    @ai_bp.response(200, AIResultSchema)
    @with_common_error_responses(ai_bp)
    def get(self, job_id):
        """AI結果取得"""
        ai_result = ai_service.get_ai_task_result(job_id)
        return ai_result

