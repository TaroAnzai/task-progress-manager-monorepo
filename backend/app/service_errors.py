from typing import Any

class ServiceError(ValueError):
    """Base class for service layer errors."""
    status_code = 500
    error_name = "Internal Server Error"

    def __init__(self, message: str|None = None):
        super().__init__(message or self.__doc__)
        self.message = message or self.__doc__

    @property
    def code(self):
        return self.status_code 

    @property
    def name(self):
        return self.error_name

    @property
    def description(self):
        return self.message

class ServiceValidationError(ServiceError):
    """Bad request from service layer."""
    status_code = 400
    error_name = "Bad request"
class ServiceAuthenticationError(ServiceError):
    """Authentication failure from service layer."""
    status_code = 401
    error_name = "Authentication failure"
class ServicePermissionError(ServiceError):
    """Permission failure from service layer."""
    status_code = 403
    error_name = "Permission failure"
class ServiceNotFoundError(ServiceError):
    """Resource not found in service layer."""
    status_code = 404
    error_name ="Resource not found"
class ServiceConflictError(ServiceError):
    """Conflict with current state or duplicated resource."""
    status_code = 409
    error_name="Conflict with current state or duplicated resource"



def format_error_response(code: int, status: str, message: str|None) -> dict[str, Any]:
    """
    エラーレスポンスのフォーマット関数
    """
    return {
        "code": code,
        "status": status,
        "errors": {
            "json":{
                "message": [message]
            }
        }
    }