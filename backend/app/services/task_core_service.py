from typing import Any

from flask import current_app
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import AccessSubject, AccessSubjectType, GroupMember, TaskAccess, User, Task, Objective, UserTaskOrder, TaskAccessUser, TaskAccessOrganization
from app.utils import check_task_access
from app.constants import TaskAccessLevelEnum, StatusEnum, STATUS_LABELS
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceAuthenticationError,
    ServiceNotFoundError,
)
from sqlalchemy import and_, exists, or_, case, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError


def get_task_by_id(db_session:Session, task_id: int, user: User) -> Task:
    # Task と UserTaskOrder を join
    result = (
        db_session.query(Task, UserTaskOrder.display_order.label("user_order"))
        .outerjoin(
            UserTaskOrder,
            and_(
                UserTaskOrder.task_id == Task.id,
                UserTaskOrder.user_id == user.id
            )
        )
        .options(joinedload(Task.objective))
        .filter(Task.id == task_id, Task.is_deleted != True)
        .first()
    )

    if not result:
        raise ServiceNotFoundError("タスクが見つかりません")

    task, user_order = result  # タプルで返ってくるので分解

    # アクセス権チェック
    if not check_task_access(db_session,user, task.id, TaskAccessLevelEnum.VIEW):
        raise ServicePermissionError("このタスクを閲覧する権限がありません")

    # ユーザーごとの order を Task に反映
    if user_order is not None:
        task.display_order = user_order

    # アクセスレベルを計算
    task.user_access_level = _calc_user_access_level(db_session, task, user)

    return task


def get_task_by_id_with_deleted(db_session: Session, task_id: int) -> Task|None:
    return db_session.get(Task, task_id)

def create_task(db_session: Session, data:dict[str, str], user: User):
    title = data.get('title')
    if not title:
        raise ServiceValidationError('タイトルは必須です')

    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            raise ServiceValidationError('日付の形式が正しくありません（YYYY-MM-DD）')
    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.due_date = due_date
    task.created_by = user.id
    task.organization_id = user.organization_id
    db_session.add(task)
    db_session.flush()

    db_session.query(UserTaskOrder).filter_by(user_id=user.id).update(
        {UserTaskOrder.display_order: UserTaskOrder.display_order + 1},
        synchronize_session='fetch'
    )
    user_task_order = UserTaskOrder()
    user_task_order.user_id = user.id
    user_task_order.task_id = task.id
    user_task_order.display_order = 0
    db_session.add(user_task_order)
    db_session.commit()

    return task


def update_task(db_session: Session, task_id: int, data: dict[str, Any], user: User):
    task = get_task_by_id(db_session, task_id, user)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(db_session, user, task.id, TaskAccessLevelEnum.FULL):
        raise ServicePermissionError('このタスクを編集する権限がありません')

    if 'status' in data:
        try:
            task.status = StatusEnum[data['status']] if isinstance(data['status'], str) else StatusEnum(data['status'])
        except (KeyError, ValueError):
            raise ServiceValidationError('ステータスが不正です')
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'due_date' in data:
        try:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            raise ServiceValidationError('日付の形式が正しくありません（YYYY-MM-DD）')
    if 'display_order' in data:
        task.display_order = data['display_order']

    db_session.commit()
    return task


def _can_delete_task(db_session: Session, task_id: int) -> bool:
    return not (
        db_session.execute(select(exists(Objective.task_id == task_id))).scalar()
    )

def delete_task(db_session: Session, task_id: int, user: User, force: bool = False):
    task = get_task_by_id(db_session, task_id, user)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(db_session, user, task.id, TaskAccessLevelEnum.FULL):
        raise ServicePermissionError('このタスクを削除する権限がありません')

    if force:
        if not _can_delete_task(db_session, task_id):
            raise ServiceValidationError('このタスクは関連するオブジェクティブが存在するため、完全に削除できません。')

        try:
            orders = db_session.query(UserTaskOrder).filter_by(task_id=task_id).all()
            for order in orders:
                db_session.delete(order)
            db_session.flush()
            db_session.query(TaskAccessUser).filter_by(task_id=task_id).delete()
            db_session.query(TaskAccessOrganization).filter_by(task_id=task_id).delete()
            db_session.delete(task)
            db_session.commit()
        except IntegrityError as e:
            db_session.rollback()
            raise ServiceValidationError(f"Cannot delete task due to foreign key constraint.:{e}")
    else:
        task.soft_delete()
        db_session.commit()

def get_tasks(db_session: Session, user: User) -> list[Task]:
    current_app.logger.info("[START] get_tasks called")

    if not user or not user.is_authenticated:
        raise ServiceAuthenticationError('ログインが必要です')

    org_id = user.organization_id
    user_id = user.id

    filter_conditions = [
        Task.created_by == user_id,
        Task.id.in_(
            db_session.query(TaskAccessUser.task_id)
            .filter(TaskAccessUser.user_id == user_id)
            .filter(TaskAccessUser.access_level.in_([
                TaskAccessLevelEnum.VIEW,
                TaskAccessLevelEnum.EDIT,
                TaskAccessLevelEnum.FULL,
            ]))
        ),
        Task.id.in_(
            db_session.query(TaskAccessOrganization.task_id)
            .filter(TaskAccessOrganization.organization_id == org_id)
            .filter(
                TaskAccessOrganization.access_level.in_([
                    TaskAccessLevelEnum.VIEW,
                    TaskAccessLevelEnum.EDIT,
                    TaskAccessLevelEnum.FULL,
                ])
            )
        )
    ]

    visible_tasks = (
        db_session.query(Task, UserTaskOrder.display_order.label('user_order'))
        .outerjoin(UserTaskOrder, and_(
            UserTaskOrder.task_id == Task.id,
            UserTaskOrder.user_id == user_id
        ))
        .options(joinedload(Task.objective)) 
        .filter(
            and_(
                Task.is_deleted != True,
                or_(*filter_conditions)
            )
        )
        .order_by(
            case((UserTaskOrder.display_order == None, 1), else_=0),  # NULLは後ろへ
            UserTaskOrder.display_order.asc(),
            case((Task.display_order == None, 1), else_=0),
            Task.display_order.asc()
        )
        .all()
    )

    result = []
    for task, user_order in visible_tasks:
        task.user_access_level = _calc_user_access_level(db_session, task, user)
        task.display_order = user_order if user_order is not None else task.display_order
        result.append(task)
    return result

def _calc_user_access_level(db_session: Session, task: Task, user: User) -> TaskAccessLevelEnum:
    if task.created_by == user.id:
        return TaskAccessLevelEnum.FULL
     # TaskAccess + Subject をJOINで取得
    stmt = (
        select(TaskAccess, AccessSubject)
        .join(AccessSubject, TaskAccess.subject_id == AccessSubject.id)
        .where(TaskAccess.task_id == task.id)
    )

    rows= db_session.execute(stmt).tuples().all()

    # ユーザーの所属グループを事前取得
    group_ids = set(
        db_session.scalars(
            select(GroupMember.group_id).where(GroupMember.user_id == user.id)
        ).all()
    )

    best_scope = None

    for access, subject in rows:

        if subject.subject_type == AccessSubjectType.USER:
            if subject.ref_id == user.id:
                best_scope = _max_scope(best_scope, access.access_level)

        elif subject.subject_type == AccessSubjectType.ORGANIZATION:
            if subject.ref_id == user.organization_id:
                best_scope = _max_scope(best_scope, access.access_level)

        elif subject.subject_type == AccessSubjectType.GROUP:
            if subject.ref_id in group_ids:
                best_scope = _max_scope(best_scope, access.access_level)

    return best_scope or TaskAccessLevelEnum.VIEW
def _max_scope(a: TaskAccessLevelEnum | None, b: TaskAccessLevelEnum) -> TaskAccessLevelEnum:
    if a is None:
        return b
    return a if a.value >= b.value else b




def update_objective_order(db_session: Session, task_id: int, data: dict[str, list[int]]) -> dict[str, str]:
    new_order = data.get('order')
    if new_order is None:
        raise ServiceValidationError('orderフィールドが必要です')
    if new_order == []:
        raise ServiceValidationError('orderフィールドは空のリストを許可しません')
    objectives = db_session.query(Objective).filter_by(task_id=task_id).filter(Objective.is_deleted != True).all()
    obj_dict = {obj.id: obj for obj in objectives}

    for index, obj_id in enumerate(new_order):
        obj = obj_dict.get(obj_id)
        if obj:
            obj.display_order = index
        else:
            raise ServiceNotFoundError(f'Objective ID {obj_id} が見つかりません')

    db_session.commit()
    return {'message': '表示順を更新しました'}

def get_statuses():
    return [
        {
            "id": status.value,         # 数値（例: 1）
            "enum": status.name,        # Enum名（例: "NOT_STARTED"）
            "label": STATUS_LABELS.get(status, "-")  # 表示用ラベル（例: "未着手"）
        }
        for status in StatusEnum
    ]
