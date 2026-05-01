# app/services/objectives_service.py
from datetime import datetime
from app.models import db, Objective, Task, User, ProgressUpdate
from app.utils import check_task_access
from app.constants import TaskAccessLevelEnum, StatusEnum, STATUS_LABELS
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
from sqlalchemy.orm import aliased
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError


def get_task_by_id(task_id):
    return Task.query.filter_by(id=task_id, is_deleted=False).first()


def get_task_by_id_with_deleted(task_id):
    return db.session.get(Task, task_id)


def get_objective_by_id(objective_id):
    return Objective.query.filter_by(id=objective_id, is_deleted=False).first()


def get_objective_by_id_with_deleted(objective_id):
    return db.session.get(Objective, objective_id)


def create_objective(data, user):
    title = data.get('title')
    task_id = data.get('task_id')

    if not title or not task_id:
        raise ServiceValidationError('タイトル・タスクIDは必須です')

    task = get_task_by_id(task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(user, task, TaskAccessLevelEnum.EDIT):
        raise ServicePermissionError('このタスクにオブジェクティブを追加する権限がありません')

    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            raise ServiceValidationError('日付の形式が正しくありません（YYYY-MM-DD）')

    max_order = db.session.query(db.func.max(Objective.display_order)) \
        .filter_by(task_id=task_id).scalar()
    new_order = (max_order or 0) + 1

    objective = Objective(
        task_id=task_id,
        title=title,
        due_date=due_date,
        assigned_user_id=data.get('assigned_user_id'),
        display_order=new_order,
        status = data.get('status'),
    )

    db.session.add(objective)
    db.session.commit()

    return {
        'message': 'オブジェクティブを追加しました',
        'objective': objective,
    }


def update_objective(objective_id, data, user):
    objective = get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')
    task = get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not check_task_access(user, task, TaskAccessLevelEnum.EDIT):
        raise ServicePermissionError('編集権限がありません')

    objective.title = data.get('title', objective.title)
    if 'due_date' in data:
        try:
            objective.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            raise ServiceValidationError('日付の形式が正しくありません（YYYY-MM-DD）')
    if 'assigned_user_id' in data:
        objective.assigned_user_id = data['assigned_user_id']
    if 'status' in data:
        objective.status = data['status']

    db.session.commit()
    return {
        'message': 'オブジェクティブを更新しました',
        'objective': objective
        }

def get_objectives_for_task(task_id, user):
    task = get_task_by_id(task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(user, task, TaskAccessLevelEnum.VIEW):
        raise ServicePermissionError('閲覧権限がありません')
    
    # 最新のProgressUpdateのサブクエリ
    latest_progress_subquery = db.session.query(
        ProgressUpdate.objective_id,
        ProgressUpdate.detail.label('latest_progress'),
        ProgressUpdate.report_date.label('latest_report_date'),
        func.row_number().over(
            partition_by=ProgressUpdate.objective_id,
            order_by=ProgressUpdate.created_at.desc()
        ).label('rn')
    ).filter(
        ProgressUpdate.is_deleted == False
    ).subquery()
    
    # 最新の1件のみを取得するサブクエリ
    latest_progress_filtered = db.session.query(
        latest_progress_subquery.c.objective_id,
        latest_progress_subquery.c.latest_progress,
        latest_progress_subquery.c.latest_report_date
    ).filter(
        latest_progress_subquery.c.rn == 1
    ).subquery()
    
    # メインクエリ
    objectives = db.session.query(Objective)\
        .outerjoin(User, Objective.assigned_user_id == User.id)\
        .outerjoin(latest_progress_filtered, 
                  Objective.id == latest_progress_filtered.c.objective_id)\
        .add_columns(
            User.name.label('assigned_user_name'),
            latest_progress_filtered.c.latest_progress,
            latest_progress_filtered.c.latest_report_date
        )\
        .filter(
            Objective.task_id == task_id,
            Objective.is_deleted == False
        )\
        .order_by(Objective.display_order)\
        .all()
    
    # 結果を整形
    objective_list = []
    for obj_data in objectives:
        objective = obj_data[0]  # Objectiveインスタンス
        # 追加データを動的に設定
        objective.assigned_user_name = obj_data[1]
        objective.latest_progress = obj_data[2]
        objective.latest_report_date = obj_data[3]
        objective_list.append(objective)
    
    return {'objectives': objective_list}
def get_objective(objective_id, user):
    objective = get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')

    task = get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(user, task, TaskAccessLevelEnum.VIEW):
        raise ServicePermissionError('閲覧権限がありません')

    return objective

def _can_delete_objective(objective_id: int) -> bool:
    return not (
        db.session.execute(select(exists(ProgressUpdate.objective_id == objective_id))).scalar()
    )
def delete_objective(objective_id:int, user: User, force: bool=False):
    objective = get_objective_by_id(objective_id)
    if not objective:
        raise ServiceNotFoundError('オブジェクティブが見つかりません')
    task = get_task_by_id(objective.task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')

    if not check_task_access(user, task, TaskAccessLevelEnum.EDIT):
        raise ServicePermissionError('削除権限がありません')

    if force == True:
        if not _can_delete_objective(objective.id):
            raise ServiceValidationError('このオブジェクティブは関連する進捗更新が存在するため、完全に削除できません。')
        try:
            db.session.delete(objective)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ServiceValidationError(f"Cannot delete objective due to foreign key constraint.:{e}")
    else:
        objective.soft_delete()
        db.session.commit()
    # reorder display order 
    remaining = Objective.query.filter_by(task_id=task.id, is_deleted=False) \
                                .order_by(Objective.display_order).all()
    for idx, obj in enumerate(remaining):
        obj.display_order = idx
    db.session.commit()

    return {'message': 'オブジェクティブを削除し、順序を更新しました'}

