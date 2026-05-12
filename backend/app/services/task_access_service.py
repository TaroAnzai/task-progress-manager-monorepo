from typing import Any, Iterable

from sqlalchemy import  select, delete, tuple_, case
from sqlalchemy.orm import Session
from app.models import AccessSubject, AccessSubjectType, Group, GroupMember, Task, TaskAccess, User, Organization
from app.utils import check_task_access, access_level_sufficient
from app.constants import TaskAccessLevelEnum
from app.service_errors import (
    ServicePermissionError,
    ServiceNotFoundError,
    ServiceValidationError,
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

def _load_required_subjects(
    db_session: Session,
    accesses: Iterable[dict[str, Any]]
) -> dict[tuple[Any, int], AccessSubject]:
    """
    必要なAccessSubjectのみを取得する。

    Returns:
        {
            (subject_type, ref_id): AccessSubject
        }
    """

    requested_keys = {
        (
            access["subject_type"],
            access["ref_id"]
        )
        for access in accesses
    }

    if not requested_keys:
        return {}

    conditions = [
        (subject_type, ref_id)
        for subject_type, ref_id in requested_keys
    ]

    subjects = db_session.scalars(
        select(AccessSubject).where(
            tuple_(
                AccessSubject.subject_type,
                AccessSubject.ref_id
            ).in_(conditions)
        )
    ).all()

    return {
        (subject.subject_type, subject.ref_id): subject
        for subject in subjects
    }
def update_access_level(db_session:Session, task_id:int, data:dict[str,list[dict[str,Any]]], user:User):
    task = _get_task_by_id(db_session, task_id)
    seen: set[tuple[AccessSubjectType, int]] = set()
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(db_session,user, task.id, TaskAccessLevelEnum.FULL):
        raise ServicePermissionError('スコープ権限を変更する権限がありません')
    for access in data['accesses']:
        key = (access["subject_type"], access['ref_id'])
        if key in seen:
            raise ServiceValidationError(
                f"アクセス対象が重複しています: "
                f"subject_type={access['subject_type'].name}, "
                f"ref_id={access['ref_id']}"
            )
        seen.add(key)

    db_session.execute(
        delete(TaskAccess)
        .where(TaskAccess.task_id == task_id)
    )
    existing_subjects = _load_required_subjects(db_session, data['accesses'])

    for subject_data in data["accesses"]:
        ref_id = subject_data["ref_id"]
        subject_type = subject_data["subject_type"]
        access_level = subject_data["access_level"]

        subject = existing_subjects.get((subject_type, ref_id))

        if not subject:
            subject = AccessSubject()
            subject.ref_id = ref_id
            subject.subject_type=subject_type
            db_session.add(subject)
            db_session.flush()
            existing_subjects[(subject_type, ref_id)] = subject
        
        task_access = TaskAccess()
        task_access.task_id = task_id
        task_access.subject_id = subject.id
        task_access.access_level = access_level
        db_session.add(task_access)

    
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
def get_tasl_access(db_session:Session, task_id:int):
    stmt = (
        select(
            TaskAccess.id.label("id"),
            AccessSubject.id.label("subject_id"),
            AccessSubject.subject_type.label("subject_type"),
            AccessSubject.ref_id.label("ref_id"),
            TaskAccess.access_level.label("access_level"),
            case(
                (
                    AccessSubject.subject_type == AccessSubjectType.USER,
                    User.name,
                ),
                (
                    AccessSubject.subject_type == AccessSubjectType.ORGANIZATION,
                    Organization.name,
                ),
                (
                    AccessSubject.subject_type == AccessSubjectType.GROUP,
                    Group.name,
                ),
                else_=None,
            ).label("display_name"),
        )
        .select_from(TaskAccess)
        .join(
            AccessSubject,
            AccessSubject.id == TaskAccess.subject_id,
        )
        .outerjoin(
            User,
            (User.id == AccessSubject.ref_id)
            & (AccessSubject.subject_type == AccessSubjectType.USER),
        )
        .outerjoin(
            Organization,
            (Organization.id == AccessSubject.ref_id)
            & (AccessSubject.subject_type == AccessSubjectType.ORGANIZATION),
        )
        .outerjoin(
            Group,
            (Group.id == AccessSubject.ref_id)
            & (AccessSubject.subject_type == AccessSubjectType.GROUP),
        )
        .where(TaskAccess.task_id == task_id)
    )

    rows = db_session.execute(stmt).mappings().all()

    return {
        "accesses": [dict(row) for row in rows]
    }
    
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
