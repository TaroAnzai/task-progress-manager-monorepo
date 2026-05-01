from functools import wraps
from app.schemas import ErrorResponseSchema

def with_common_error_responses(bp):
    """共通のエラーレスポンス（400,401,403）を追加する簡素版デコレーター"""
    def decorator(func):
        @bp.alt_response(400, {
            "description": "Bad Request",
            "schema": ErrorResponseSchema,
            "content_type": "application/json"
        })
        @bp.alt_response(401, {
            "description": "Unauthorized",
            "schema": ErrorResponseSchema,
            "content_type": "application/json"
        })
        @bp.alt_response(403, {
            "description": "Forbidden",
            "schema": ErrorResponseSchema,
            "content_type": "application/json"
        })
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
