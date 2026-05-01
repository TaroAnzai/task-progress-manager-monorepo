from app.models import db, Task, User, Organization, TaskAccessUser, TaskAccessOrganization
from app.utils import check_task_access, access_level_sufficient
from app.constants import TaskAccessLevelEnum
from app.service_errors import (
    ServicePermissionError,
    ServiceNotFoundError,
)


def get_task_by_id(task_id):
    return Task.query.filter_by(id=task_id, is_deleted=False).first()


def get_task_by_id_with_deleted(task_id):
    return db.session.get(Task, task_id)

# Access levels in order of increasing permission
ACCESS_LEVELS = list(TaskAccessLevelEnum)

def update_access_level(task_id, data, user):
    task = get_task_by_id(task_id)
    if not task:
        raise ServiceNotFoundError('タスクが見つかりません')
    if not check_task_access(user, task, TaskAccessLevelEnum.FULL):
        raise ServicePermissionError('スコープ権限を変更する権限がありません')

    # --- ユーザーアクセス処理 ---
    input_user_access = data.get('user_access', [])
    input_user_ids = {entry['user_id'] for entry in input_user_access}
    existing_user_entries = TaskAccessUser.query.filter_by(task_id=task_id).all()
    existing_user_map = {entry.user_id: entry for entry in existing_user_entries}

    for entry in input_user_access:
        user_id = entry['user_id']
        access_level = TaskAccessLevelEnum(entry['access_level'])
        if user_id in existing_user_map:
            existing_user_map[user_id].access_level = access_level
        else:
            db.session.add(TaskAccessUser(task_id=task_id, user_id=user_id, access_level=access_level))

    for user_id in set(existing_user_map.keys()) - input_user_ids:
        db.session.delete(existing_user_map[user_id])

    # --- 組織アクセス処理（organization_idベース） ---
    input_org_access = data.get('organization_access', [])
    input_org_ids = {entry['organization_id'] for entry in input_org_access}
    existing_org_entries = TaskAccessOrganization.query.filter_by(task_id=task_id).all()
    existing_org_map = {entry.organization_id: entry for entry in existing_org_entries}

    for entry in input_org_access:
        org_id = entry['organization_id']
        access_level = TaskAccessLevelEnum(entry['access_level'])
        if org_id in existing_org_map:
            existing_org_map[org_id].access_level = access_level
        else:
            db.session.add(TaskAccessOrganization(task_id=task_id, organization_id=org_id, access_level=access_level))

    for org_id in set(existing_org_map.keys()) - input_org_ids:
        db.session.delete(existing_org_map[org_id])

    db.session.commit()
    return {'message': 'アクセス設定を更新しました'}

def get_task_users(task_id):
    # タスクのアクセスレベルを持つユーザーを返す
    allowed_levels = [lvl for lvl in ACCESS_LEVELS if access_level_sufficient(lvl, TaskAccessLevelEnum.VIEW)]

    access_user_ids = db.session.query(TaskAccessUser.user_id).filter(
        TaskAccessUser.task_id == task_id,
        TaskAccessUser.access_level.in_(allowed_levels)
    ).all()
    access_user_ids = [uid for (uid,) in access_user_ids]

    access_org_ids = db.session.query(TaskAccessOrganization.organization_id).filter(
        TaskAccessOrganization.task_id == task_id,
        TaskAccessOrganization.access_level.in_(allowed_levels)
    ).all()
    access_org_ids = [oid for (oid,) in access_org_ids]

    org_user_ids = []
    if access_org_ids:
        org_user_ids = db.session.query(User.id).filter(User.organization_id.in_(access_org_ids)).all()
        org_user_ids = [uid for (uid,) in org_user_ids]

    total_user_ids = list(set(access_user_ids + org_user_ids))

    users = db.session.query(User).filter(User.id.in_(total_user_ids)).all()
    task = get_task_by_id_with_deleted(task_id)
    creator = db.session.get(User, task.created_by) if task else None

    if creator and creator.id not in [u.id for u in users]:
        users.append(creator)

    return users

def get_task_access_users(task_id):
    entries = db.session.query(
        User.id, User.name, User.email, TaskAccessUser.access_level
    ).join(TaskAccessUser, TaskAccessUser.user_id == User.id).filter(
        TaskAccessUser.task_id == task_id
    ).all()

    result = [{
        "user_id": u.id,
        "name": u.name,
        "access_level": u.access_level
    } for u in entries]

    return result

def get_task_access_organizations(task_id):
    entries = db.session.query(
        Organization.id, Organization.name, TaskAccessOrganization.access_level
    ).join(TaskAccessOrganization, TaskAccessOrganization.organization_id == Organization.id).filter(
        TaskAccessOrganization.task_id == task_id
    ).all()

    result = [{
        "organization_id": o.id,
        "name": o.name,
        "access_level": o.access_level
    } for o in entries]

    return result
