from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models import GroupMember, Group, GroupScopeType, Organization, User
from typing import Any, List

from app.service_errors import ServicePermissionError, ServiceValidationError
from app.utils import get_ancestor_organization_ids, get_descendant_organizations

def _can_view_group(user: User, group: Group, company_id: int) -> bool:
    if user.is_superuser:
        return True

    if group.owner_user_id == user.id:
        return True

    if group.scope_type == GroupScopeType.GLOBAL:
        if user.organization is None:
            return False
        if user.organization.company_id == company_id:
            return True

    if group.scope_type == GroupScopeType.ORGANIZATION:
        if user.organization_id is None:
            return False
        allowed_org_ids = set(get_ancestor_organization_ids(user.organization_id))
        all_orgs = Organization.query.filter(Organization.is_deleted != True).all()
        descendants = get_descendant_organizations(user.organization_id, all_orgs)
        descendants_ids = [org.id for org in descendants]
        allowed_org_ids.update(descendants_ids)
        return group.organization_id in allowed_org_ids


    return False

def _build_group_member_response(db_session: Session, group_id: int) -> dict[str, Any]:
    """
    グループメンバー一覧レスポンスを組み立てる
    """
    stmt = (
        select(
            User.id,
            User.name,
            User.email,
            User.organization_id,
            Organization.name.label("organization_name"),
        )
        .join(GroupMember, GroupMember.user_id == User.id)
        .outerjoin(Organization, Organization.id == User.organization_id)
        .where(GroupMember.group_id == group_id)
        .order_by(User.name.asc())
    )

    rows = db_session.execute(stmt).all()

    users = [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "organization_id": row.organization_id,
            "organization_name": row.organization_name,
        }
        for row in rows
    ]

    return {
        "group_id": group_id,
        "user_ids": [user["id"] for user in users],
        "users": users,
    }
def get_group_members(db_session: Session, group_id: int, current_user: User):
    """
    メンバー一覧取得（UI用にまとめて返す）
    """
    stmt = (
        select(Group, Organization.company_id)
        .outerjoin(
            Organization,
            Group.organization_id == Organization.id,
        )
        .where(Group.id == group_id)
    )

    row = db_session.execute(stmt).one_or_none()
    if row is None:
        raise ServiceValidationError("Group not found")

    group, company_id = row

    if not _can_view_group(current_user, group, company_id):
        raise ServicePermissionError("User does not have permission to view this group")


    return _build_group_member_response(db_session, group_id)



def replace_group_members(db_session: Session, group_id: int, user_ids: List[int], current_user: User):
    """
    メンバー全置換
    """

    group = db_session.get(Group, group_id)
    if not group:
        raise ServiceValidationError("Group not found")

    if current_user.is_superuser is False and group.owner_user_id != current_user.id:
        raise ServicePermissionError("User does not have permission to modify this group")

    new_set = set(user_ids)

    # -------------------------
    # ユーザー存在チェック
    # -------------------------
    users = db_session.scalars(
        select(User.id).where(User.id.in_(new_set))
    ).all()

    if len(users) != len(new_set):
        raise ServiceValidationError("Some users do not exist")

    # -------------------------
    # 現在のメンバー取得
    # -------------------------
    existing = db_session.scalars(
        select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    ).all()

    existing_set = set(existing)

    # 差分
    to_add = new_set - existing_set
    to_remove = existing_set - new_set

    # -------------------------
    # 削除
    # -------------------------
    if to_remove:
        db_session.execute(
            delete(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id.in_(to_remove)
            )
        )

    # -------------------------
    # 追加
    # -------------------------
    for uid in to_add:
        group_member = GroupMember()
        group_member.group_id = group_id
        group_member.user_id = uid
        db_session.add(group_member)

    db_session.commit()

    return _build_group_member_response(db_session, group_id)
