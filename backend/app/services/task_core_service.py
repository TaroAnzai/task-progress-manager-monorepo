from typing import Any, List, Optional

from datetime import datetime
from app.models import (AccessSubject, AccessSubjectType, GroupMember,
                         TaskAccess, User, Task, Objective, UserTaskOrder,
)
from app.utils import check_task_access
from app.constants import TaskAccessLevelEnum, StatusEnum, STATUS_LABELS
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceAuthenticationError,
    ServiceNotFoundError,
)
from sqlalchemy import Integer, and_, cast, exists, or_, case, select, func, delete
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass



def get_task_by_id(db_session: Session, task_id: int, user: User) -> Task:
    """
    特定のタスクをIDで取得する。
    1. 存在チェック（Soft Delete考慮）
    2. 権限チェック（作成者 or アクセス権付与）
    3. ユーザー固有の表示順と実行権限の付与
    を、N+1を回避しつつSQL 2.0スタイルで実行する。
    """
    if not user or not user.is_authenticated:
        raise ServiceAuthenticationError('ログインが必要です')

    # 1. ユーザーの所属コンテキスト（所属組織・グループ）を解決
    # ※ get_tasksで定義した共通関数を使用
    context = _resolve_user_access_context(db_session, user)

    # 2. 権限計算用のサブクエリ（対象タスクのみに絞り込み）
    access_subq = (
        select(
            TaskAccess.task_id,
            func.max(cast(TaskAccess.access_level, Integer)).label("max_level")
        )
        .where(
            and_(
                TaskAccess.task_id == task_id,
                TaskAccess.subject_id.in_(context.subject_ids)
            )
        )
        .group_by(TaskAccess.task_id)
    ).subquery()

    # 3. メインクエリの構築
    stmt = (
        select(
            Task,
            # 作成者ならFULL、それ以外は付与された最大権限
            case(
                (Task.created_by == user.id, TaskAccessLevelEnum.FULL.value),
                else_=access_subq.c.max_level
            ).label("effective_access_level"),
            UserTaskOrder.display_order.label("user_order")
        )
        .options(joinedload(Task.objective))  # N+1回避
        .outerjoin(access_subq, Task.id == access_subq.c.task_id)
        .outerjoin(
            UserTaskOrder,
            and_(UserTaskOrder.task_id == Task.id, UserTaskOrder.user_id == user.id)
        )
        .where(
            and_(
                Task.id == task_id,
                Task.is_deleted == False
            )
        )
    )

    # 4. 実行とバリデーション
    result = db_session.execute(stmt).first()

    # A. そもそもデータが存在しない（または削除済み）場合
    if not result:
        raise ServiceNotFoundError("タスクが見つかりません")

    task = result.Task

    # B. 権限チェック
    # 作成者でもなく、どのSubject（個人・組織・班）経由でも権限がない場合
    if result.effective_access_level is None:
        raise ServicePermissionError("このタスクを閲覧する権限がありません")
    effective_level = TaskAccessLevelEnum(result.effective_access_level)
    
    # 5. 取得した動的属性をインスタンスにセット
    task.user_access_level = effective_level
    if result.user_order is not None:
        task.display_order = result.user_order

    return task

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
    # --- UserTaskOrderを一括削除 ---
            db_session.execute(
                delete(UserTaskOrder)
                .where(UserTaskOrder.task_id == task_id)
            )

            # --- TaskAccessを一括削除 ---
            db_session.execute(
                delete(TaskAccess)
                .where(TaskAccess.task_id == task_id)
            )

            # --- Task削除（ORMインスタンス前提） ---
            db_session.delete(task)

            db_session.commit()
        except IntegrityError as e:
            db_session.rollback()
            raise ServiceValidationError(f"Cannot delete task due to foreign key constraint.:{e}")
    else:
        task.soft_delete()
        db_session.commit()




@dataclass(frozen=True)
class UserAccessContext:
    """ユーザーが保持するアクセス権のコンテキスト（対象IDの集合）"""
    user_id: int
    organization_id: Optional[int]
    group_ids: List[int]
    # 解決されたAccessSubject.idのリスト
    subject_ids: List[int]

def _resolve_user_access_context(db_session: Session, user: User) -> UserAccessContext:
    """ユーザーの所属（組織・グループ）から関連するAccessSubjectのIDをすべて解決する"""
    
    # 1. ユーザー自身のグループ所属を取得
    group_ids = db_session.scalars(
        select(GroupMember.group_id).where(GroupMember.user_id == user.id)
    ).all()

    # 2. 関連するSubject(USER, ORGANIZATION, GROUP)のIDをまとめて取得
    # subject_typeとref_idのペアで、自分に関係する行を特定
    subject_conditions = [
        and_(AccessSubject.subject_type == AccessSubjectType.USER, AccessSubject.ref_id == user.id)
    ]
    if user.organization_id:
        subject_conditions.append(
            and_(AccessSubject.subject_type == AccessSubjectType.ORGANIZATION, AccessSubject.ref_id == user.organization_id)
        )
    if group_ids:
        subject_conditions.append(
            and_(AccessSubject.subject_type == AccessSubjectType.GROUP, AccessSubject.ref_id.in_(group_ids))
        )

    subject_ids = db_session.scalars(
        select(AccessSubject.id).where(or_(*subject_conditions))
    ).all()

    return UserAccessContext(
        user_id=user.id,
        organization_id=user.organization_id,
        group_ids=list(group_ids),
        subject_ids=list(subject_ids)
    )

def get_tasks(db_session: Session, user: User) -> List[Task]:
    """
    ユーザーがアクセス可能なタスク一覧を取得する。
    N+1問題を回避し、SQL側で権限の最大値計算とフィルタリングを完結させる。
    """
    if not user or not user.is_authenticated:
        raise ServiceAuthenticationError('ログインが必要です')

    # 1. アクセスコンテキストの解決
    context = _resolve_user_access_context(db_session, user)

    # 2. タスクごとの最大アクセスレベルを計算するサブクエリ
    # ユーザーが直接・組織・グループ経由で持つ権限のうち、最大のものを抽出
    # また、作成者(created_by)の場合は強制的にFULL権限とする
    access_subq = (
        select(
            TaskAccess.task_id,
            func.max(cast(TaskAccess.access_level, Integer)).label("max_level")
        )
        .where(TaskAccess.subject_id.in_(context.subject_ids))
        .group_by(TaskAccess.task_id)
    ).subquery()

    # 3. メインクエリの構築
    stmt = (
        select(
            Task,
            # 作成者ならFULL、そうでなければサブクエリから取得した最大権限を適用
            case(
                (Task.created_by == user.id, TaskAccessLevelEnum.FULL.value),
                else_=access_subq.c.max_level
            ).label("effective_access_level"),
            UserTaskOrder.display_order.label("user_order")
        )
        # 権限サブクエリとの結合（作成者自身、または権限設定があるタスクのみ）
        .outerjoin(access_subq, Task.id == access_subq.c.task_id)
        # ユーザー固有の並び順を結合
        .outerjoin(
            UserTaskOrder, 
            and_(UserTaskOrder.task_id == Task.id, UserTaskOrder.user_id == user.id)
        )
        .where(
            and_(
                Task.is_deleted == False,
                or_(
                    Task.created_by == user.id,          # 自分が作った
                    access_subq.c.max_level.is_not(None) # 何らかの閲覧権限が付与されている
                )
            )
        )
        .order_by(
            case((UserTaskOrder.display_order.is_(None), 1), else_=0),
            UserTaskOrder.display_order.asc(),
            case((Task.display_order.is_(None), 1), else_=0),
            Task.display_order.asc()
        )
    )

    # 4. 実行と結果の加工
    results = db_session.execute(stmt).all()

    final_tasks = []
    for row in results:
        task = row.Task


        # クエリで計算した権限と表示順をエンティティにセット
        task.user_access_level = TaskAccessLevelEnum(row.effective_access_level)
        if row.user_order is not None:
            task.display_order = row.user_order
        final_tasks.append(task)
    return final_tasks



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
