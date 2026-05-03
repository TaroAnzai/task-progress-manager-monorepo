# utils.py

from sqlalchemy.orm import Session
from sqlalchemy import select, exists, and_, or_
from .models import (
    AccessSubject, 
    AccessSubjectType, GroupMember, TaskAccess, db, TaskAccessUser, TaskAccessOrganization, Organization, User, Task)
from .constants import OrgRoleEnum, TaskAccessLevelEnum
from .constants import (
    TaskAccessLevelEnum,
    OrgRoleEnum,
)

def get_all_child_organizations(org_id):
    """
    指定された org_id の下位すべての組織ID一覧を再帰的に取得するユーティリティ関数
    """
    org_ids = set()
    queue = [org_id]

    while queue:
        current = queue.pop()
        org_ids.add(current)
        children = Organization.query.filter(Organization.parent_id==current).all()
        for child in children:
            if child.id not in org_ids:
                queue.append(child.id)

    return list(org_ids)

def get_descendant_organizations(root_id, all_orgs):
    """
    root_id を起点に、その下位の組織（自身を含む）をすべて返す
    """
    descendants = []

    # 自身の組織を追加
    root_org = next((org for org in all_orgs if org.id == root_id), None)
    if root_org:
        descendants.append(root_org)

    # 親IDベースのマップを作成
    org_map = {}
    for org in all_orgs:
        parent = org.parent_id
        org_map.setdefault(parent, []).append(org)

    def recurse(parent_id):
        for child in org_map.get(parent_id, []):
            descendants.append(child)
            recurse(child.id)

    recurse(root_id)
    return descendants

def can_view_task(user, task):
    """
    ユーザーが指定されたタスクを閲覧可能かどうかを判定する
    """
    if task.created_by == user.id:
        return True

    if any(s.role == OrgRoleEnum.SYSTEM_ADMIN for s in user.access_scopes):
        return True

    if any(s.role == OrgRoleEnum.ORG_ADMIN for s in user.access_scopes):
        all_orgs = Organization.query.all()
        descendant_orgs = get_descendant_organizations(user.organization_id, all_orgs)
        descendant_ids = [org.id for org in descendant_orgs]
        if task.organization_id in descendant_ids:
            return True

    user_scope = db.session.query(TaskAccessUser).filter_by(task_id=task.id, user_id=user.id).first()
    org_scope = db.session.query(TaskAccessOrganization).filter_by(task_id=task.id, organization_id=user.organization_id).first()

    if user_scope or org_scope:
        return True

    return False

def can_edit_task(user, task):
    """
    ユーザーが指定されたタスクを編集可能かどうかを判定する
    """
    if task.created_by == user.id:
        return True

    if any(s.role == OrgRoleEnum.SYSTEM_ADMIN for s in user.access_scopes):
        return True

    if any(s.role == OrgRoleEnum.ORG_ADMIN for s in user.access_scopes):
        all_orgs = Organization.query.all()
        descendant_orgs = get_descendant_organizations(user.organization_id, all_orgs)
        descendant_ids = [org.id for org in descendant_orgs]
        return task.organization_id in descendant_ids

    return False

def check_task_access(
    db_session: Session,
    user: User,
    task_id: int,
    required_level: TaskAccessLevelEnum
) -> bool:
    """
    DBクエリでアクセス判定（高速版）
    """

    # 作成者チェック（即return）
    if user.id:
        creator_check = select(Task.id).where(
            Task.id == task_id,
            Task.created_by == user.id
        ).limit(1)

        if db_session.execute(creator_check).first():
            return True

    # -------------------------
    # group_id一覧取得（事前に1回）
    # -------------------------
    group_ids = db_session.scalars(
        select(GroupMember.group_id).where(
            GroupMember.user_id == user.id
        )
    ).all()

    # -------------------------
    # subject条件
    # -------------------------
    conditions = []

    # USER
    conditions.append(
        and_(
            AccessSubject.subject_type == AccessSubjectType.USER,
            AccessSubject.ref_id == user.id
        )
    )

    # ORGANIZATION
    if user.organization_id:
        conditions.append(
            and_(
                AccessSubject.subject_type == AccessSubjectType.ORGANIZATION,
                AccessSubject.ref_id == user.organization_id
            )
        )

    # GROUP
    if group_ids:
        conditions.append(
            and_(
                AccessSubject.subject_type == AccessSubjectType.GROUP,
                AccessSubject.ref_id.in_(group_ids)
            )
        )

    # -------------------------
    # existsクエリ
    # -------------------------
    stmt = select(
        exists().where(
            TaskAccess.task_id == task_id,
            TaskAccess.access_level >= required_level,
            TaskAccess.subject_id == AccessSubject.id,
            or_(*conditions)
        )
    )

    return bool(db_session.execute(stmt).scalar())

def access_level_sufficient(user_level: TaskAccessLevelEnum, required_level: TaskAccessLevelEnum) -> bool:
    """Return ``True`` if ``user_level`` satisfies ``required_level``."""
    if not isinstance(user_level, TaskAccessLevelEnum):
        user_level = TaskAccessLevelEnum(user_level)
    if not isinstance(required_level, TaskAccessLevelEnum):
        required_level = TaskAccessLevelEnum(required_level)

    return user_level >= required_level

def check_org_access(user: User, organization_id: int, required_role: OrgRoleEnum = OrgRoleEnum.MEMBER) -> bool:
    """Return True if user has required_role for organization_id.

    SYSTEM_ADMIN: 同一会社全組織にアクセス可能
    ORG_ADMIN: 自組織＋子組織にアクセス可能
    MEMBER: 自組織のみ
    """
    if getattr(user, "is_superuser", False):
        return True

    target_org = db.session.get(Organization, organization_id)
    if not target_org:
        return False

    highest_role: OrgRoleEnum = OrgRoleEnum.MEMBER  # 最小値（Enum定義に応じて）

    for scope in user.access_scopes:
        if scope.role == OrgRoleEnum.SYSTEM_ADMIN:
            scope_org = scope.organization or db.session.get(Organization, scope.organization_id)
            if scope_org and scope_org.company_id == target_org.company_id:
                return True  # 即時アクセス許可

        elif scope.role == OrgRoleEnum.ORG_ADMIN:
            base_id = scope.organization_id or user.organization_id
            descendant_ids = get_all_child_organizations(base_id)
            descendant_ids.append(base_id)  # 自組織を含める
            if organization_id in descendant_ids:
                highest_role = max(highest_role, OrgRoleEnum.ORG_ADMIN)

        elif scope.organization_id == organization_id:
            highest_role = max(highest_role, OrgRoleEnum.MEMBER)

    return highest_role >= required_role


def require_superuser(user):
    if not getattr(user, 'is_superuser', False):
        return False
    return True




