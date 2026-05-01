# app/services/reminder_service.py
from __future__ import annotations

from datetime import datetime, timezone, time as dtime
from typing import Any, Dict, Tuple, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import ObjectiveReminderSetting, ObjectiveReminderLog
from app.models import Objective, Task, TaskAccessLevelEnum  # Task/Objective は実体に合わせて
from app.utils import check_task_access
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
from app.reminder_constants import ReminderConditionEnum, ReminderFrequencyEnum

# ----------------------------
# 内部ユーティリティ
# ----------------------------

def _utcnow():
    return datetime.now(timezone.utc)

def _get_objective_or_404(objective_id: int) -> Objective:
    obj = Objective.query.filter_by(id=objective_id, is_deleted=False).first()
    if not obj:
        raise ServiceNotFoundError("Objective not found")
    return obj

def _get_setting_or_404(setting_id: int) -> ObjectiveReminderSetting:
    setting = (
        db.session.query(ObjectiveReminderSetting)
        .options(joinedload(ObjectiveReminderSetting.objective).joinedload(getattr(Objective, "task", None)))
        .filter(ObjectiveReminderSetting.id == setting_id)
        .first()
    )
    if not setting:
        raise ServiceNotFoundError("Reminder setting not found")
    return setting

def _get_task_from_objective(obj: Objective) -> Task:
    task = getattr(obj, "task", None)
    if not task:
        raise ServiceNotFoundError("Task not found")
    return task

def _require_view_permission(user, objective: Objective):
    task = _get_task_from_objective(objective)
    if not (check_task_access(user, task, TaskAccessLevelEnum.VIEW) or user.id == getattr(objective, "assigned_user_id", None)):
        raise ServicePermissionError("You do not have permission to view this objective/reminders.")

def _require_edit_or_assigned(user, objective: Objective):
    task = _get_task_from_objective(objective)
    if not (check_task_access(user, task, TaskAccessLevelEnum.EDIT) or user.id == getattr(objective, "assigned_user_id", None)):
        raise ServicePermissionError("You do not have permission to modify this objective/reminders.")

from datetime import time as dtime
from typing import Any, Dict, Optional

from app.reminder_constants import ReminderConditionEnum, ReminderFrequencyEnum
from app.service_errors import (
    ServiceValidationError,
    ServiceAuthenticationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
from app.models import ObjectiveReminderSetting

def _validate_business(
    payload: Dict[str, Any],
    existing: Optional[ObjectiveReminderSetting] = None
) -> Dict[str, Any]:
    """
    スキーマで基本型は保証されている前提。
    - Enumは“厳密に”Enumメンバーのみ許可（文字列や数値は不可）
    - PATCH時は existing の値でフォールバック
    - 依存必須（NO_UPDATE→threshold_days / INTERVAL→interval_days）
    - 値域チェック（>=1）
    - 送信時刻の型補正（"HH:MM[:SS]" を許容、通常は fields.Time で time 渡し）
    - OVERDUE のとき threshold_days は必ず None
    """

    # 1) Enumの取得（PATCHで未指定なら既存値を使う）
    cond = payload.get("condition_type", getattr(existing, "condition_type", None))
    freq = payload.get("frequency_type", getattr(existing, "frequency_type", None))

    if not isinstance(cond, ReminderConditionEnum):
        raise ServiceValidationError("invalid condition_type")
    if not isinstance(freq, ReminderFrequencyEnum):
        raise ServiceValidationError("invalid frequency_type")

    # 2) 依存パラメータ（PATCHで未指定なら既存値）
    th = payload.get("threshold_days") if "threshold_days" in payload else getattr(existing, "threshold_days", None)
    iv = payload.get("interval_days")  if "interval_days"  in payload else getattr(existing, "interval_days",  None)

    # 3) 依存必須チェック
    if cond == ReminderConditionEnum.NO_UPDATE and th is None:
        raise ServiceValidationError("threshold_days is required for NO_UPDATE")
    if freq == ReminderFrequencyEnum.INTERVAL and iv is None:
        raise ServiceValidationError("interval_days is required for INTERVAL")

    # 4) 値域チェック（任意だが安全）
    if th is not None and th < 0:
        raise ServiceValidationError("threshold_days must be >= 0")
    if iv is not None and iv < 1:
        raise ServiceValidationError("interval_days must be >= 1")

    # 5) 送信時刻の型補正（通常は already time 型）
    st = payload.get("send_time_local", getattr(existing, "send_time_local", None))
    if isinstance(st, str):
        parts = st.split(":")
        try:
            if len(parts) == 2:
                payload["send_time_local"] = dtime(int(parts[0]), int(parts[1]), 0)
            elif len(parts) == 3:
                payload["send_time_local"] = dtime(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                raise ValueError
        except Exception:
            raise ServiceValidationError("send_time_local must be 'HH:MM' or 'HH:MM:SS'")

    # 7) 正規化した値を戻す（payload内の型を明確化）
    payload["condition_type"] = cond
    payload["frequency_type"] = freq

    return payload



def _prevent_duplicate(objective_id: int, payload: Dict[str, Any], exclude_id: Optional[int] = None):
    """
    同一Objectiveで完全重複設定の作成を抑止（任意）
    """
    q = db.session.query(ObjectiveReminderSetting).filter(
        ObjectiveReminderSetting.objective_id == objective_id,
        ObjectiveReminderSetting.condition_type == payload.get("condition_type"),
        ObjectiveReminderSetting.frequency_type == payload.get("frequency_type"),
        ObjectiveReminderSetting.send_time_local == payload.get("send_time_local"),
        ObjectiveReminderSetting.is_active == (payload.get("is_active", True)),
    )
    # NO_UPDATE の場合だけ threshold_days が比較対象
    if payload.get("condition_type") == ReminderConditionEnum.NO_UPDATE.name:
        q = q.filter(ObjectiveReminderSetting.threshold_days == payload.get("threshold_days"))
    # INTERVAL の場合だけ interval_days が比較対象
    if payload.get("frequency_type") == ReminderFrequencyEnum.INTERVAL.name:
        q = q.filter(ObjectiveReminderSetting.interval_days == payload.get("interval_days"))

    if exclude_id:
        q = q.filter(ObjectiveReminderSetting.id != exclude_id)

    exists = db.session.query(q.exists()).scalar()
    if exists:
        raise ServiceValidationError("重複するリマインド設定が既に存在します。")


# ----------------------------
# 公開サービス関数（route と同名）
# ----------------------------

def list_objective_reminders(objective_id: int, user) -> Tuple[Dict[str, Any], int]:
    if not user or not getattr(user, "is_authenticated", False):
        raise ServicePermissionError("ログインが必要です")

    objective = _get_objective_or_404(objective_id)
    _require_view_permission(user, objective)

    items: List[ObjectiveReminderSetting] = (
        db.session.query(ObjectiveReminderSetting)
        .filter(ObjectiveReminderSetting.objective_id == objective_id)
        .order_by(ObjectiveReminderSetting.id.asc())
        .all()
    )
    return {
        "items": items,
        "total": len(items),
    }, 200


def create_objective_reminder(objective_id: int, payload: Dict[str, Any], user) -> Tuple[ObjectiveReminderSetting, int]:
    if not user or not getattr(user, "is_authenticated", False):
        raise ServicePermissionError("ログインが必要です")

    objective = _get_objective_or_404(objective_id)
    _require_edit_or_assigned(user, objective)

    data = _validate_business(dict(payload))
    if "send_time_local" not in data or data["send_time_local"] is None:
        data["send_time_local"] = dtime(9, 0, 0)  # 既定 09:00:00

    _prevent_duplicate(objective_id, data)

    setting = ObjectiveReminderSetting(
        objective_id=objective_id,
        condition_type=data["condition_type"],
        threshold_days=data.get("threshold_days"),
        frequency_type=data["frequency_type"],
        interval_days=data.get("interval_days"),
        send_time_local=data["send_time_local"],
        is_active=bool(data.get("is_active", True)),
        last_sent_at=None,
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.session.add(setting)
    db.session.commit()
    return setting, 201


def get_reminder(setting_id: int, user) -> Tuple[ObjectiveReminderSetting, int]:
    if not user or not getattr(user, "is_authenticated", False):
        raise ServicePermissionError("ログインが必要です")

    setting = _get_setting_or_404(setting_id)
    _require_view_permission(user, setting.objective)
    return setting, 200


def update_reminder(setting_id: int, payload: Dict[str, Any], user) -> Tuple[ObjectiveReminderSetting, int]:
    if not user or not getattr(user, "is_authenticated", False):
        raise ServicePermissionError("ログインが必要です")
    print("payload",payload)
    setting = _get_setting_or_404(setting_id)
    _require_edit_or_assigned(user, setting.objective)

    data = _validate_business(dict(payload), existing=setting)
    print("data",data)
    # 重複チェック（自分自身は除外）
    _prevent_duplicate(setting.objective_id, data, exclude_id=setting.id)

    # 反映
    for k in ("condition_type", "threshold_days", "frequency_type", "interval_days", "send_time_local", "is_active"):
        if k in data:
            setattr(setting, k, data[k])

    setting.updated_at = _utcnow()
    db.session.commit()
    return setting, 200


def delete_reminder(setting_id: int, user) -> Tuple[Dict[str, Any], int]:
    if not user or not getattr(user, "is_authenticated", False):
        raise ServicePermissionError("ログインが必要です")

    setting = _get_setting_or_404(setting_id)
    _require_edit_or_assigned(user, setting.objective)

    # 履歴が存在する場合は削除禁止 → 無効化を案内（FK 制約の可能性も考慮）
    has_logs = (
        db.session.query(ObjectiveReminderLog.id)
        .filter(ObjectiveReminderLog.setting_id == setting.id)
        .limit(1)
        .first()
    )
    if has_logs:
        raise ServiceValidationError("送信履歴が存在するため削除できません。停止（is_active=False）をご利用ください。")

    db.session.delete(setting)
    db.session.commit()
    return {"deleted": True}, 204
