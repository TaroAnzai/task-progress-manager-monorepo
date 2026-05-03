from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, select

from app.models import Group, GroupMember, GroupScopeType, User
from typing import Any

from app.constants import OrgRoleEnum
from app.service_errors import ServicePermissionError, ServiceValidationError
from app.utils import check_org_access


def list_groups(db_session: Session, current_user: User):

    if current_user.is_superuser:
        return db_session.scalars(select(Group)).all()

    stmt = select(Group).where(
        or_(
            # PRIVATE → ownerのみ
            and_(
                Group.scope_type == GroupScopeType.PRIVATE,
                Group.owner_user_id == current_user.id
            ),

            # ORGANIZATION → 同一organization
            and_(
                Group.scope_type == GroupScopeType.ORGANIZATION,
                Group.organization_id == current_user.organization_id
            ),

            # GLOBAL → 全員
            Group.scope_type == GroupScopeType.GLOBAL
        )
    )

    return db_session.scalars(stmt).all()


def get_group(db_session: Session, group_id: int):
    group = db_session.get(Group, group_id)
    if not group:
        raise ServiceValidationError("Group not found")
    return group


def create_group(db_session: Session, data: dict[str, Any], current_user: User):
    """
    グループ作成 + メンバー作成
    """
    # Valisation: sope_type & organization_id
    if data["scope_type"] == GroupScopeType.GLOBAL:
        if current_user.is_superuser is False:
            raise ServicePermissionError("Only superusers can create global groups")
    elif data["scope_type"] == GroupScopeType.ORGANIZATION:
        org_id:int|None = data.get("organization_id")
        if org_id is None:
            raise ServiceValidationError("organization_id is required for ORGANIZATION scope_type")
        if check_org_access(current_user, org_id, OrgRoleEnum.ORG_ADMIN) is False:
            raise ServicePermissionError("User does not have access to the specified organization")

    

    # -------------------------
    # Group作成
    # -------------------------
    group = Group()
    group.name = data["name"]
    group.scope_type = data["scope_type"]
    group.organization_id = data.get("organization_id")
    group.owner_user_id = current_user.id

    db_session.add(group)
    db_session.flush()  # group.id取得

    # -------------------------
    # メンバー作成
    # -------------------------
    user_ids = set(data["member_user_ids"])

    # ユーザー存在チェック（重要）
    users = db_session.scalars(
        select(User.id).where(User.id.in_(user_ids))
    ).all()

    if len(users) != len(user_ids):
        raise ServiceValidationError("Some users do not exist")

    for uid in user_ids:
        group_member = GroupMember()
        group_member.group_id = group.id
        group_member.user_id = uid
        db_session.add(group_member)

    db_session.commit()

    return group


def update_group(db_session: Session, group_id: int, data: dict[str, Any], current_user: User):
    group = db_session.get(Group, group_id)
    if not group:
        raise ServiceValidationError("Group not found")
    if current_user.is_superuser is False and group.owner_user_id != current_user.id:
        raise ServicePermissionError("Only superusers or the group owner can update the group")
    # -------------------------
    # 更新
    # -------------------------
    if "name" in data:
        group.name = data["name"]

    if "scope_type" in data:
        group.scope_type = data["scope_type"]

    if "organization_id" in data:
        group.organization_id = data["organization_id"]

    db_session.commit()

    return group


def delete_group(db_session: Session, group_id: int, current_user: User):
    group = db_session.get(Group, group_id)
    if not group:
        raise ServiceValidationError("Group not found")

    if current_user.is_superuser is False and group.owner_user_id != current_user.id:
        raise ServicePermissionError("Only superusers or the group owner can delete the group")

    db_session.delete(group)
    db_session.commit()