from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models import GroupMember, Group, GroupScopeType, User
from typing import List

from backend.app.service_errors import ServicePermissionError, ServiceValidationError

def _can_view_group(user: User, group: Group) -> bool:
    if user.is_superuser:
        return True

    if group.owner_user_id == user.id:
        return True

    if group.scope_type == GroupScopeType.GLOBAL:
        return True

    if group.scope_type == GroupScopeType.ORGANIZATION:
        return (
            user.organization_id is not None
            and group.organization_id == user.organization_id
        )

    return False
def get_group_members(db_session: Session, group_id: int, current_user: User):
    """
    メンバー一覧取得（UI用にまとめて返す）
    """
    group = db_session.get(Group, group_id)
    if not group:
        raise ServiceValidationError("Group not found")
    if _can_view_group(current_user, group) == False:
        raise ServicePermissionError("User does not have permission to view this group")

    user_ids = db_session.scalars(
        select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    ).all()

    return {
        "group_id": group_id,
        "user_ids": user_ids
    }


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

    return {
        "group_id": group_id,
        "user_ids": list(new_set)
    }