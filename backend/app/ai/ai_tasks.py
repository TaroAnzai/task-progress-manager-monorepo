# app/ai/ai_tasks.py
import traceback

from app.celery_app import celery
from app.ai.gemini_client import GeminiAISuggestionClient
from app.schemas.ai_schemas import AISuggestionMode

@celery.task(bind=True)
def run_ai_suggestion(self, task_info: dict, mode:str ) -> dict:
    try:
        if not isinstance(task_info, dict):
            raise ValueError(f"task_info must be dict, got {type(task_info)}")

        client = GeminiAISuggestionClient()

        if mode == AISuggestionMode.TASK_NAME.value:
            result = client.suggest_task_name(task_info)
        elif mode == AISuggestionMode.OBJECTIVES.value:
            result = client.generate_objectives(task_info)
        else:
            raise ValueError(f"Invalid mode: {mode}")

        return {
            "status": "success",
            "mode": mode,
            "result": result
            }

    except Exception as e:
        print(f"[AI_TASK ERROR] {e}")
        traceback.print_exc() 
        return {"status": "error", "message": str(e)}