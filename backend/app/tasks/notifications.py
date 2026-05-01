# app/tasks/notifications.py
from datetime import datetime, timedelta
from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import joinedload
from app.celery_app import celery
from app import create_app, db
from app.models import Objective, ObjectiveReminderSetting, ObjectiveReminderLog, User, ProgressUpdate,Task
from app.util.mailer import MailConfig, MailMessage, send_email, MailSendError
import os
from app.reminder_constants import ReminderConditionEnum, ReminderFrequencyEnum
from sqlalchemy import func
from app.constants import StatusEnum
# テンプレート読み込み
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "util", "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml", "txt"])
)
text_template = env.get_template("reminder_mail.txt")
html_template = env.get_template("reminder_mail.html")

@celery.task(name="app.tasks.notifications.reminder_task")
def reminder_task():
    """
    5分ごとに実行されるリマインドメールタスク
    DBのリマインド設定を参照し、対象ユーザーにリマインドを送信する
    """
    app = create_app()
    with app.app_context():
        now = datetime.now()
        sent_count = 0

        # --- 最新 ProgressUpdate を取るサブクエリ ---
        latest_progress_subquery = (
            db.session.query(
                ProgressUpdate.objective_id,
                ProgressUpdate.report_date.label("latest_report_date"),
                func.row_number().over(
                    partition_by=ProgressUpdate.objective_id,
                    order_by=ProgressUpdate.report_date.desc()
                ).label("rn")
            )
            .filter(ProgressUpdate.is_deleted == False)
            .subquery()
        )

        latest_progress_filtered = (
            db.session.query(
                latest_progress_subquery.c.objective_id,
                latest_progress_subquery.c.latest_report_date,
            )
            .filter(latest_progress_subquery.c.rn == 1)
            .subquery()
        )

        # --- リマインド設定と Objective を join ---
        rows = (
            db.session.query(
                ObjectiveReminderSetting,
                Objective,
                Task,
                latest_progress_filtered.c.latest_report_date
            )
            .join(Objective, ObjectiveReminderSetting.objective_id == Objective.id)
            .join(Task, Objective.task_id == Task.id)
            .outerjoin(latest_progress_filtered, Objective.id == latest_progress_filtered.c.objective_id)
            .filter(ObjectiveReminderSetting.is_active == True)
            .filter(Objective.is_deleted == False)  # ✅ Objective削除除外
            .filter(Task.is_deleted == False)       # ✅ Task削除除外
            .filter(
                Objective.status.notin_([
                    StatusEnum.COMPLETED,
                    StatusEnum.SAVED
                ])
            )  # ✅ Objectiveステータス除外
            .filter(
                Task.status.notin_([
                    StatusEnum.COMPLETED,
                    StatusEnum.SAVED
                ])
            )  # ✅ Taskステータス除外
            .all()
        )
        for setting, obj, latest_report_date in rows:
            obj = setting.objective
            if not obj:
                continue

            should_send = False

            # condition_type に応じて判定
            if setting.condition_type == ReminderConditionEnum.OVERDUE:
                if obj.due_date and now.date() > obj.due_date:
                    # threshold_days で猶予をつける
                    overdue_days = (now.date() - obj.due_date).days
                    if overdue_days >= (setting.threshold_days or 0):
                        should_send = True

            elif setting.condition_type == ReminderConditionEnum.NO_UPDATE:
                if latest_report_date:
                    no_update_days = (now.date() - latest_report_date).days
                    if no_update_days >= (setting.threshold_days or 0):
                        should_send = True
                else:
                    # 一度も更新がない場合
                    if setting.threshold_days == 0:
                        should_send = True
            if not should_send:
                continue

            # frequency_type に応じて送信間隔を確認
            if setting.frequency_type == ReminderFrequencyEnum.ONCE:
                already_sent = (
                    db.session.query(ObjectiveReminderLog)
                    .filter_by(reminder_setting_id=setting.id)
                    .first()
                )
                if already_sent:
                    continue  # 1回送信済みなのでスキップ

            elif setting.frequency_type == ReminderFrequencyEnum.INTERVAL:
                last_sent = (
                    db.session.query(ObjectiveReminderLog)
                    .filter_by(setting_id=setting.id)
                    .order_by(ObjectiveReminderLog.sent_at.desc())
                    .first()
                )
                if last_sent and (now - last_sent.sent_at) < timedelta(days=setting.interval_days or 1):
                    continue  # インターバル未経過

            # ここで実際のメール送信処理を呼び出す（仮実装はprint）
            print(f"Send reminder to Objective({obj.id}) - {obj.title}")
            # --- 宛先 ---
            user = db.session.get(User, obj.assigned_user_id or obj.created_by)
            print(f"  To: {user.email if user else 'No User'}")
            if not user or not user.email:
                continue
            # --- 本文生成 ---
            context = {
                "user_name": user.name,
                "objective_title": obj.title,
                "due_date": obj.due_date or "未設定",
                "latest_report_date": latest_report_date or "未報告"
            }
            body_text = text_template.render(**context)
            body_html = html_template.render(**context)
            # --- メール送信 ---
            try:
                msg = MailMessage(
                    subject="[リマインド] 目標の進捗確認",
                    to=[user.email],   # ✅ 宛先
                    text=body_text,  # ✅ プレーンテキスト本文
                    html=body_html   # ✅ HTML本文
                )
                mail_config = MailConfig.from_config(current_app.config)
                send_email(msg, mail_config)
                print(f"[{now}] Sent reminder to {user.email} for Objective({obj.id})")

                log = ObjectiveReminderLog(
                    setting_id=setting.id,
                    objective_id=obj.id,
                    user_id=user.id,
                    condition_type=setting.condition_type,
                    sent_at=now,
                    status="SUCCESS",          # 成功時
                    error_message=None
                )
                db.session.add(log)
                sent_count += 1

            except MailSendError as e:
                print(f"[{now}] Failed to send email to {user.email}: {e}")
                log = ObjectiveReminderLog(
                    setting_id=setting.id,
                    objective_id=obj.id,
                    user_id=user.id if user else None,
                    condition_type=setting.condition_type,
                    sent_at=now,
                    status="FAILURE",      # 失敗時
                    error_message=str(e)
                )
                db.session.add(log)

        db.session.commit()

        return {"status": "ok", "sent_count": sent_count, "time": now.isoformat()}