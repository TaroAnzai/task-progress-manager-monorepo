# config.py
import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# 先に環境を取得（デフォルトは development）
#print("=== Config init debug ===")
env = os.getenv("FLASK_ENV", "development")

# 環境別
if env == "testing":
    load_dotenv(BASE_DIR / ".env.test", override=True)
elif env == "production":
    load_dotenv(BASE_DIR / ".env.prod", override=True)
else:  # development
    load_dotenv(BASE_DIR / ".env.dev", override=True)



def str_to_bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val
    return val.lower() in ("true", "1", "yes")
class Config:
    URL_PREFIX = os.getenv("URL_PREFIX", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Database
    DB_FILE = os.getenv("DB_FILE", "app.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL is required")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is required")
    origins = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS = origins if origins == "*" else origins.split(",")
    CORS_SUPPORTS_CREDENTIALS = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "None")
    if SESSION_COOKIE_SAMESITE == "None":
        SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = str_to_bool(os.getenv("SESSION_COOKIE_HTTPONLY", "true"))

    # OpenAPI/Swagger 設定
    API_TITLE = os.getenv("API_TITLE", "Task Progress API")
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    OPENAPI_VERSION = os.getenv("OPENAPI_VERSION", "3.0.3")
    OPENAPI_URL_PREFIX = os.getenv("OPENAPI_URL_PREFIX", "/doc")
    OPENAPI_JSON_PATH = os.getenv("OPENAPI_JSON_PATH", "openapi.json")
    OPENAPI_REDOC_PATH = os.getenv("OPENAPI_REDOC_PATH", "/redoc")
    OPENAPI_REDOC_URL = os.getenv("OPENAPI_REDOC_URL","https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js")
    OPENAPI_SWAGGER_UI_PATH = os.getenv("OPENAPI_SWAGGER_UI_PATH", "/swagger-ui")
    OPENAPI_SWAGGER_UI_URL = os.getenv(
        "OPENAPI_SWAGGER_UI_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")  # redis://redis:6379/1
    CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")  # redis://redis:6379/1
    # SMTP
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "30"))
    # Mail
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_REPLY_TO = os.getenv("MAIL_REPLY_TO")
    MAIL_RETURN_PATH = os.getenv("MAIL_RETURN_PATH")

    # Gemini API
    GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL=os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    TESTING = os.getenv("TESTING", "false").lower() == "true"
    WTF_CSRF_ENABLED = (
        os.getenv("WTF_CSRF_ENABLED", "").lower() == "true"
        if os.getenv("WTF_CSRF_ENABLED") is not None
        else not TESTING
    )
