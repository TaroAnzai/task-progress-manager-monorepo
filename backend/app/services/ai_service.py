# app/services/ai_service.py

from celery.result import AsyncResult
from app.ai.ai_tasks import run_ai_suggestion
from app.celery_app import celery
from app.service_errors import ServiceValidationError
from app.schemas.ai_schemas import AISuggestionMode
from dateutil import parser
def enqueue_ai_task(data: dict):
    """
    AI提案処理をCeleryにキューイング
    """
    task_info = data.get("task_info")
    mode_name = data.get("mode").value
    date_str = task_info.get("deadline") 
    if (date_str):
        try:
            parser.parse(date_str, fuzzy=False)
        except (ValueError, TypeError):
            raise ServiceValidationError("Invalid date format")

    if not task_info:
        raise ServiceValidationError("task_info が指定されていません")

    result = run_ai_suggestion.apply_async(args=[task_info, mode_name])

    return {"job_id": result.id}


def get_ai_task_result(job_id: str):
    result = AsyncResult(job_id, app=celery)
    
    base_response = {
        "async_result": {
            "job_id": result.id,
            "state": result.state,
            "ready": result.ready(),
            "successful": result.successful(),
            "date_done": result.date_done,
            "message": str(result.result) if result.failed() else None,
        }
    }

    if result.state == "PENDING":
        base_response["status"] = "PENDING"
        return base_response

    if result.state == "SUCCESS" and result.result:
        data = result.result
        
        if not isinstance(data, dict):
            return base_response
            
        if data.get("status") == "success":
            mode = AISuggestionMode(data["mode"])
            base_response.update({
                "status": "SUCCESS",
                "mode": mode
            })
            
            if mode == AISuggestionMode.TASK_NAME:
                base_response["task_title_data"] = data["result"]
            elif mode == AISuggestionMode.OBJECTIVES:
                base_response["objectives_data"] = data["result"]
                
        elif data.get("status") == "error":
            base_response.update({
                "status": "ERROR",
                "error": data.get("message")
            })
    
    return base_response