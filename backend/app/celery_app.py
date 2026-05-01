# celery_app.py

import os
from celery import Celery
from celery.schedules import crontab

# print("=== Celery init debug ===")
# print("CELERY_BROKER_URL:", os.getenv("CELERY_BROKER_URL"))
# print("CELERY_RESULT_BACKEND:", os.getenv("CELERY_RESULT_BACKEND"))

def make_celery():
    celery = Celery(__name__)
    
    celery.conf.update(
        broker_url=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
        task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", False),
        task_eager_propagates=os.getenv("CELERY_TASK_EAGER_PROPAGATES", False),
        task_ignore_result=os.getenv("CELERY_TASK_IGNORE_RESULT", False),

        timezone="Asia/Tokyo",
        task_routes={
            "app.tasks.notifications.*": {"queue": "mail"},
            "app.tasks.ai.*": {"queue": "ai"}, 
        },
        beat_schedule={
            "progress-reminder-every-5min": {
                "task": "app.tasks.notifications.reminder_task",
                "schedule": crontab(minute="*/5"),  # 5分ごとに実行
                "options": {"queue": "mail"},
            },
        },
        broker_connection_retry_on_startup=True,
    )

    celery.autodiscover_tasks(["app.tasks","app.ai"])
    # ---- 明示的にインポート（確実に登録させる） ----
    celery.conf.imports = (
        "app.tasks.notifications",
        "app.ai.ai_tasks",
    )
    return celery

# Celeryインスタンス作成
celery = make_celery()