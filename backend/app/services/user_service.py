# services/user_service.py

from flask import current_app
import re
from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload
from ..models import Objective, ObjectiveReminderLog, ProgressUpdate, Task, db, User, Organization, AccessScope, Company
from ..utils import (
    get_all_child_organizations,
    get_descendant_organizations,
    check_org_access,
)
from ..constants import OrgRoleEnum
from ..service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
import re
from app.constants import OrgRoleEnum  # enum 定義を利用
from sqlalchemy.exc import IntegrityError

def _is_email_taken(norm_email: str, exclude_user_id: int | None = None) -> bool:
    q = User.query.with_entities(User.id).filter(User.normalized_email == norm_email)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    return db.session.query(q.exists()).scalar()

def is_valid_email(email):
    # シンプルな正規表現（RFC全準拠ではなく一般的な形式の検出）
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def create_user(data, current_user: User):
    if not current_user:
        raise ServiceNotFoundError('ログインユーザーが見つかりません')
    #組織の項目のチェック
    org_id = data.get('organization_id')
    if not org_id:
        raise ServiceValidationError('organization_idは必須です')
    # 組織管理権限チェック
    if not check_org_access(current_user, data.get('organization_id'), OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    wp_user_id = data.get('wp_user_id')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', OrgRoleEnum.MEMBER)  # ← デフォルトはMEMBER

    # 必須項目チェック
    if not is_valid_email(email):
        raise ServiceValidationError('無効なメールアドレス形式です') 
    norm = email.strip().lower()

    if _is_email_taken(norm):
        # ここでUX的に早く返す
        raise ServiceValidationError("このメールアドレスは既に使用されています。")

    if role not in OrgRoleEnum.__members__.values() and role not in OrgRoleEnum.__members__:
        raise ServiceValidationError(f'指定されたroleが不正です: {role}')

    if wp_user_id and User.query.filter_by(wp_user_id=wp_user_id).first():
        raise ServiceValidationError('この wp_user_id は既に使用されています')
    
    org = db.session.get(Organization, org_id)
    if not org:
        raise ServiceValidationError('指定された組織IDが存在しません')


    # --- ユーザー登録 ---
    user = User(
        wp_user_id=wp_user_id,
        name=name,
        email=email,
        organization_id=org_id
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # user.id をAccessScope登録に使用するため

    # --- AccessScope登録 ---
    access_scope = AccessScope(
        user_id=user.id,
        organization_id=org_id,
        role=role if isinstance(role, OrgRoleEnum) else OrgRoleEnum(role)
    )
    db.session.add(access_scope)

    db.session.commit()

    return {'message': 'ユーザーを登録しました', 'user': user}




def get_user_by_id(user_id, current_user):
    user = db.session.get(User, user_id)
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    if not check_org_access(current_user, user.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    return user

def update_user(user_id, data, current_user):
    user = db.session.get(User, user_id)
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    if not check_org_access(current_user, user.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    if 'name' in data:
        user.name = data['name']

    if 'wp_user_id' in data:
        if User.query.filter(User.wp_user_id == data['wp_user_id'], User.id != user_id).first():
            raise ServiceValidationError('この wp_user_id は既に使用されています')
        user.wp_user_id = data['wp_user_id']

    if 'organization_id' in data:
    # organization_id の変更後の値を取得しておく
        new_org_id = data.get('organization_id', user.organization_id)
        new_org = db.session.get(Organization, new_org_id)
        if not new_org:
            raise ServiceValidationError('指定された組織IDが存在しません')
        user.organization_id = new_org_id

    if 'email' in data:
        if not is_valid_email(data['email']):
            raise ServiceValidationError('無効なメールアドレス形式です') 
        norm = data['email'].strip().lower()
        if _is_email_taken(norm):
            raise ServiceValidationError("このメールアドレスは既に使用されています。")

        user.email = data['email']

    if 'password' in data and data['password']:
        user.set_password(data['password'])

    db.session.commit()
    return user


def can_delete_user(user_id: int) -> bool:
    return not (
        db.session.execute(select(exists(Task.created_by == user_id))).scalar() or
        db.session.execute(select(exists(Objective.assigned_user_id == user_id))).scalar() or
        db.session.execute(select(exists(Objective.created_by == user_id))).scalar() or
        db.session.execute(select(exists(ProgressUpdate.updated_by == user_id))).scalar() or
        db.session.execute(select(exists(ObjectiveReminderLog.user_id == user_id))).scalar()
    )
def delete_user(user_id, current_user, force = False):
    user = db.session.get(User, user_id)
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    if not check_org_access(current_user, user.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    if force:
        if not can_delete_user(user_id):
            raise ServiceValidationError('関連するタスクや目標が存在するため、ユーザーを完全に削除できません。')
        try:
            db.session.query(AccessScope).filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
            return {'message': 'ユーザーと関連スコープを削除しました'}
        except IntegrityError as e:
            db.session.rollback()
            raise ServiceValidationError(f'関連データがあるため削除に失敗しました: {e}')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"delete_user error: {e}")
            raise ServiceValidationError(f'削除に失敗しました: {e}')
    else:
        user.soft_delete()
        db.session.commit()
    return {'message': 'ユーザーを削除しました'}

def get_users(user):
    #userが所属しているcompanyの全ユーザーを返す。
    requesting_user_id = user.id
    organization_id = user.organization_id
    organization = db.session.get(Organization,organization_id)
    company_id = organization.company_id
    requester = db.session.get(User, requesting_user_id)
    if not requester:
        return []

    # スーパーユーザーなら全ユーザーを返す
    if requester.is_superuser:
        query = db.session.query(User).options(joinedload(User.organization))
        if company_id:
            query = query.join(Organization).filter(Organization.company_id == company_id)
        query = query.filter(User.is_deleted == False, Organization.is_deleted == False)
        return query.all()
    if not company_id:
        raise ServiceNotFoundError(f'Not found company.会社が見つかりません')
    #スーパーユーザー以外ならcompanyのユーザーを返す。
    query = db.session.query(User).options(joinedload(User.organization))
    query = query.join(Organization).filter(Organization.company_id == company_id)

    #スコープを追加
    query = query.filter(User.is_deleted == False, Organization.is_deleted == False)
    users = query.all()
    return users


def get_user_by_email(email, current_user):
    norm = email.strip().lower()
    user = User.query.filter(User.normalized_email== norm, User.is_deleted != True).first()
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    if not check_org_access(current_user, user.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')
    return user

def get_user_by_wp_user_id(wp_user_id, current_user):
    user = User.query.filter(User.wp_user_id==wp_user_id, User.is_deleted != True).first()
    if not user:
        raise ServiceNotFoundError('ユーザーが見つかりません')

    if not check_org_access(current_user, user.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    return user

def get_users_by_org_tree(org_id, current_user):
    if not check_org_access(current_user, org_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    try:
        org_ids = get_all_child_organizations(org_id)
        users = User.query.filter(User.organization_id.in_(org_ids), User.is_deleted != True).all()
        return users
    except Exception as e:
        raise ServiceValidationError(str(e))
     
def get_user_for_admin(user, query_args):
    requesting_user_id = user.id
    company_id = query_args.get('company_id')
    organization_id = user.organization_id
    requester = db.session.get(User, requesting_user_id)
    if not requester:
        return []

    # スーパーユーザーなら全ユーザーを返す
    if requester.is_superuser:
        query = db.session.query(User).options(joinedload(User.organization))
        if company_id:
            query = query.join(Organization).filter(Organization.company_id == company_id)
        query = query.filter(User.is_deleted == False, Organization.is_deleted != True)
        return query.all()

    # system-admin ロールのチェック
    system_admin_scope = next(
        (s for s in requester.access_scopes if s.role == OrgRoleEnum.SYSTEM_ADMIN), None
    )
    if system_admin_scope:
        company_id = system_admin_scope.organization.company_id
        orgs = (
            Organization.query
            .filter(Organization.company_id==company_id, Organization.is_deleted != True)
            .all()
        )
        org_ids = [org.id for org in orgs]
        return (
            User.query
            .options(joinedload(User.organization))
            .filter(User.organization_id.in_(org_ids), User.is_deleted != True)
            .all()
        )

    # 通常の組織管理者（ORG_ADMIN）なら所属組織＋子組織のみ
    if not check_org_access(requester, organization_id or requester.organization_id, OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError('権限がありません')

    all_orgs = Organization.query.filter(Organization.is_deleted != True).all()
    base_org_id = organization_id or requester.organization_id
    base_org = db.session.get(Organization, base_org_id)
    if not base_org:
        raise ServiceNotFoundError('組織が見つかりません')

    descendants = get_descendant_organizations(base_org.id, all_orgs)
    org_ids = [org.id for org in descendants]

    users = (
        User.query
        .options(joinedload(User.organization))
        .filter(User.organization_id.in_(org_ids), User.is_deleted != True)
        .all()
    )

    return users