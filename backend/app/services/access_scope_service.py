# app/services/access_scope_service.py

from ..models import db, User, AccessScope, Organization
from ..constants import OrgRoleEnum
from ..service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceNotFoundError,
)

def get_user_scopes(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    return list(user.access_scopes)

def add_access_scope_to_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    org_id = data.get('organization_id')
    role = data.get('role')

    if not org_id or not role:
        raise ServiceValidationError('organization_id と role は必須です')

    existing_scope = AccessScope.query.filter_by(user_id=user.id, organization_id=org_id).first()
    if existing_scope:
        if existing_scope.role != OrgRoleEnum(role):
            existing_scope.role = OrgRoleEnum(role)
            db.session.commit()
            return {'message': 'アクセススコープを更新しました'}
        return {'message': 'すでにこのアクセススコープは登録されています'}

    try:
        role_enum = OrgRoleEnum(role)
    except ValueError:
        raise ServiceValidationError('無効な role です')

    new_scope = AccessScope(user_id=user.id, organization_id=org_id, role=role_enum)
    db.session.add(new_scope)
    db.session.commit()
    return {'message': 'アクセススコープを追加しました'}

def delete_access_scope(scope_id):
    scope = db.session.get(AccessScope, scope_id)
    if not scope:
        raise ServiceNotFoundError('スコープが見つかりません')

    db.session.delete(scope)
    db.session.commit()
    return {'message': 'アクセススコープを削除しました'}
