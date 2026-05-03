from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import AccessSubject, AccessSubjectType, GroupMember, Task, TaskAccess, User, Organization
from app.utils import check_task_access, access_level_sufficient
from app.constants import TaskAccessLevelEnum
from app.service_errors import (
    ServicePermissionError,
    ServiceNotFoundError,
)

# Access levels in order of increasing permission
ACCESS_LEVELS = list(TaskAccessLevelEnum)

def _get_task_by_id(db_session:Session, task_id:int):
    stmt = select(Task).where(
        Task.id == task_id,
        Task.is_deleted == False
    )
    return db_session.scalars(stmt).first()


def _get_task_by_id_with_deleted(db_session:Session, task_id:int):
    return db_session.get(Task, task_id)

def _set_task_access_level(
    db: Session,
    task_id: int,
    subject_type: AccessSubjectType,
    ref_id: int,
    access_level: TaskAccessLevelEnum,
) -> None:
    """
    タスクのアクセスレベルを設定（更新 or 新規作成）
    """

    # =========================
    # 1. AccessSubject取得 or 作成
    # =========================
    stmt = select(AccessSubject).where(
        AccessSubject.subject_type == subject_type,
        AccessSubject.ref_id == ref_id,
    )
    subject = db.scalar(stmt)

    if subject is None:
        subject = AccessSubject()
        subject.subject_type = subject_type
        subject.ref_id = ref_id
        db.add(subject)
        db.flush()  # id確定

    # =========================
    # 2. TaskAccess取得
    # =========================
    stmt = select(TaskAccess).where(
        TaskAccess.task_id == task_id,
        TaskAccess.subject_id == subject.id,
    )
    task_access = db.scalar(stmt)

    # =========================
    # 3. 更新 or 新規作成
    # =========================
    if task_access:
        task_access.access_level = access_level
    else:
        task_access = TaskAccess()
        task_access.task_id = task_id
        task_access.subject_id = subject.id
        task_access.access_level = access_level
        db.add(task_access)

    db.flush()

def _remove_task_access(
    db: Session,
    task_id: int,
    subject_type: AccessSubjectType,
    ref_id: int,
):
    stmt = select(AccessSubject).where(
        AccessSubject.subject_type == subject_type,
        AccessSubject.ref_id == ref_id,
    )
    subject = db.scalar(stmt)

    if not subject:
        return

    stmt = select(TaskAccess).where(
        TaskAccess.task_id == task_id,
        TaskAccess.subject_id == subject.id,
    )
    task_access = db.scalar(stmt)

    if task_access:
        db.delete(task_access)

def update_access_level(db_session:Session, task_id:int, data:dict[str, Any], user:User):
    task = _get_task_by_id(db_session, task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(db_session,user, task.id, TaskAccessLevelEnum.FULL):
        raise ServicePermissionError('スコープ権限を変更する権限がありません')

    # --- ユーザーアクセス処理 ---
    input_user_access = data.get('user_access', [])
    input_user_ids = {entry['user_id'] for entry in input_user_access}
    stmt = (
        select(User.id)
        .select_from(TaskAccess)
        .join(
            AccessSubject,
            (TaskAccess.subject_id == AccessSubject.id)
            & (AccessSubject.subject_type == AccessSubjectType.USER)
        )
        .join(User, AccessSubject.ref_id == User.id)
        .where(TaskAccess.task_id == task_id)
    )
    existing_user_ids = set(db_session.execute(stmt).scalars())

    
    for entry in input_user_access:
        _set_task_access_level(
            db_session,
            task_id,
            AccessSubjectType.USER,
            entry['user_id'],
            TaskAccessLevelEnum(entry['access_level'])
        )

    for user_id in existing_user_ids - input_user_ids:
        _remove_task_access(
            db_session,
            task_id,
            AccessSubjectType.USER,
            user_id
        )

    # --- 組織アクセス処理（organization_idベース） ---
    input_org_access = data.get('organization_access', [])
    input_org_ids = {entry['organization_id'] for entry in input_org_access}
    stmt = (
        select(AccessSubject.ref_id)
        .select_from(TaskAccess)
        .join(
            AccessSubject,
            (TaskAccess.subject_id == AccessSubject.id)
            & (AccessSubject.subject_type == AccessSubjectType.ORGANIZATION)
        )
        .where(TaskAccess.task_id == task_id)
    )
    existing_org_ids = set(db_session.execute(stmt).scalars())

    for entry in input_org_access:
        _set_task_access_level(
            db_session,
            task_id,
            AccessSubjectType.ORGANIZATION,
            entry['organization_id'],
            TaskAccessLevelEnum(entry['access_level'])
        )

    for org_id in existing_org_ids - input_org_ids:
        _remove_task_access(
            db_session,
            task_id,
            AccessSubjectType.ORGANIZATION,
            org_id
        )

    db_session.commit()
    return {'message': 'アクセス設定を更新しました'}

def get_task_users(db: Session, task_id: int) -> list[User]:
    """
    タスクにアクセス可能なユーザー一覧を取得
    """

    # =========================
    # 1. VIEW以上のアクセスレベルを抽出
    # =========================
    allowed_levels = [
        lvl for lvl in ACCESS_LEVELS
        if access_level_sufficient(lvl, TaskAccessLevelEnum.VIEW)
    ]

    # =========================
    # 2. TaskAccess + Subject JOIN
    # =========================
    stmt = (
        select(TaskAccess, AccessSubject)
        .join(AccessSubject, TaskAccess.subject_id == AccessSubject.id)
        .where(
            TaskAccess.task_id == task_id,
            TaskAccess.access_level.in_(allowed_levels),
        )
    )

    rows = db.execute(stmt).tuples().all()

    user_ids: set[int] = set()
    org_ids: set[int] = set()
    group_ids: set[int] = set()

    # =========================
    # 3. subjectごとに振り分け
    # =========================
    for _, subject in rows:
        if subject.subject_type == AccessSubjectType.USER:
            user_ids.add(subject.ref_id)

        elif subject.subject_type == AccessSubjectType.ORGANIZATION:
            org_ids.add(subject.ref_id)

        elif subject.subject_type == AccessSubjectType.GROUP:
            group_ids.add(subject.ref_id)

    # =========================
    # 4. organization配下ユーザー取得
    # =========================
    if org_ids:
        stmt = select(User.id).where(User.organization_id.in_(org_ids))
        org_user_ids = db.scalars(stmt).all()
        user_ids.update(org_user_ids)
    # =========================
    #  group配下ユーザー取得
    # =========================
    if group_ids:
        stmt = select(GroupMember.user_id).where(
            GroupMember.group_id.in_(group_ids)
        )
        group_user_ids = db.scalars(stmt).all()
        user_ids.update(group_user_ids)
    # =========================
    # 5. ユーザー取得
    # =========================
    users: list[User] = []
    if user_ids:
        stmt = select(User).where(User.id.in_(user_ids))
        users = list(db.scalars(stmt).all())

    # =========================
    # 6. 作成者追加
    # =========================
    task = _get_task_by_id_with_deleted(db, task_id)
    if task:
        creator = db.get(User, task.created_by)
        if creator and creator.id not in {u.id for u in users}:
            users.append(creator)

    return users

def get_task_access_users(db_session: Session, task_id: int):
    stmt = (
        select(User.id, User.name, TaskAccess.access_level)
        .join(
            AccessSubject,
            (TaskAccess.subject_id == AccessSubject.id)
            & (AccessSubject.subject_type == AccessSubjectType.USER)
        )
        .join(User, AccessSubject.ref_id == User.id)
        .where(TaskAccess.task_id == task_id)
    )
    rows = db_session.execute(stmt).tuples().all()
    result = [
        {
            "user_id": uid,
            "name": name,
            "access_level": level,
        }
        for uid, name, level in rows
    ]

    return result

def get_task_access_organizations(db_session: Session, task_id: int):
    stmt = (
        select(Organization.id, Organization.name, TaskAccess.access_level)
        .join(
            AccessSubject,
            (TaskAccess.subject_id == AccessSubject.id)
            & (AccessSubject.subject_type == AccessSubjectType.ORGANIZATION)
        )
        .join(Organization, AccessSubject.ref_id == Organization.id)
        .where(TaskAccess.task_id == task_id)
    )




    entries = db_session.execute(stmt).tuples().all()

    result = [{
        "organization_id": id,
        "name": name,
        "access_level": access_level
    } for id, name, access_level in entries]

    return result
