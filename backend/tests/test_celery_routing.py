from app.celery_app import celery


def test_ai_suggestion_task_routes_to_ai_queue():
    route = celery.amqp.router.route(
        {}, "app.ai.ai_tasks.run_ai_suggestion", args=(), kwargs={}
    )

    assert route["queue"].name == "ai"


def test_reminder_task_routes_to_mail_queue():
    route = celery.amqp.router.route(
        {}, "app.tasks.notifications.reminder_task", args=(), kwargs={}
    )

    assert route["queue"].name == "mail"
