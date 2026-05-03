# app/services/progress_updates_service.py
from app.models import db, Objective, Task, ProgressUpdate, User
from app.utils import check_task_access
from app.constants import TaskAccessLevelEnum, StatusEnum
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

def _get_task_by_id(task_id:int) -> Task|None:
    return Task.query.filter_by(id=task_id, is_deleted=False).first()


def _get_task_by_id_with_deleted(task_id:int) -> Task|None:
    return db.session.get(Task, task_id)


def _get_objective_by_id(objective_id:int) -> Objective|None:
    return Objective.query.filter_by(id=objective_id, is_deleted=False).first()


def _get_objective_by_id_with_deleted(objective_id:int) -> Objective|None:
    return db.session.get(Objective, objective_id)


def _get_progress_by_id(progress_id:int) -> ProgressUpdate|None:
    return ProgressUpdate.query.filter_by(id=progress_id, is_deleted=False).first()


def _get_progress_by_id_with_deleted(progress_id:int) -> ProgressUpdate|None:
    return db.session.get(ProgressUpdate, progress_id)


def add_progress(db_session: Session, objective_id:int, data:dict, user:User):
    objective = _get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')
    task = _get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not (
        check_task_access(db_session, user, task.id, TaskAccessLevelEnum.EDIT)
        or user.id == objective.assigned_user_id
    ):
        raise ServicePermissionError('進捗追加の権限がありません')

    progress = ProgressUpdate()
    progress.objective_id = objective_id
    progress.status = data['status']
    progress.detail = data['detail']
    progress.report_date = data['report_date']
    progress.updated_by = user.id
    
    db.session.add(progress)
    db.session.commit()
    return {'message': '進捗を追加しました'}


def get_progress_list(db_session: Session, objective_id: int, user: User):
    objective = _get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')

    task = _get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not check_task_access(db_session, user, task.id, TaskAccessLevelEnum.VIEW):
        raise ServicePermissionError('閲覧権限がありません')

    progress_list = ProgressUpdate.query.filter_by(objective_id=objective_id, is_deleted=False).all()
    result = []

    for p in progress_list:
        try:
            label = StatusEnum(p.status) # 例: "IN_PROGRESS"
        except ValueError:
            label = StatusEnum["UNDEFINED"]

        updated_by_user = db.session.get(User, p.updated_by)
        updated_by = updated_by_user.name if updated_by_user else "不明"

        result.append({
            'id': p.id,
            'status': label,
            'detail': p.detail,
            'report_date': p.report_date,
            'updated_by': updated_by
        })

    return result




def get_latest_progress(db_session: Session, objective_id: int, user: User):
    objective = _get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')

    task = _get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not check_task_access(db_session, user, task.id, TaskAccessLevelEnum.VIEW):
        raise ServicePermissionError('閲覧権限がありません')

    progress = (
        ProgressUpdate.query
        .filter_by(objective_id=objective_id, is_deleted=False)
        .order_by(ProgressUpdate.report_date.desc(), ProgressUpdate.created_at.desc())
        .first()
    )

    if not progress:
        return {
            'status': None,
            'report_date': None,
            'detail': None,
            'updated_by': None
        }

    # status は IntEnum型として保存されているのでそのまま使用
    try:
        status_label = StatusEnum(progress.status)
    except ValueError:
        status_label = StatusEnum["UNDEFINED"]

    updated_by_user = db.session.get(User, progress.updated_by)
    user_name = updated_by_user.name if updated_by_user else "不明"

    return {
        'status': status_label,
        'report_date': progress.report_date,
        'updated_by': user_name,
        'detail': progress.detail
    }

def delete_progress(db_session: Session, progress_id: int, user: User, force: bool = False):
    progress = _get_progress_by_id(progress_id)
    if not progress:
        raise ServiceNotFoundError('進捗が見つかりません')
    objective = _get_objective_by_id_with_deleted(progress.objective_id)
    if not objective or objective.is_deleted:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')
    task = _get_task_by_id_with_deleted(objective.task_id)
    if not task or task.is_deleted:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not check_task_access(db_session, user, task.id, TaskAccessLevelEnum.EDIT):
        raise ServicePermissionError('削除権限がありません')
    if force == True:
        try:
            db.session.delete(progress)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ServiceValidationError(f"Cannot delete progress due to foreign key constraint.:{e}")
    else:
        progress.soft_delete()
        db.session.commit()

    return {'message': '進捗を削除しました'}
