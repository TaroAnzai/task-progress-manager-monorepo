from sqlalchemy import exists, select

from app.models import Company, User, db, Organization
from flask import jsonify, g
from sqlalchemy.exc import IntegrityError
from app.service_errors import (
    ServiceValidationError,
    ServiceAuthenticationError,
    ServicePermissionError,
    ServiceNotFoundError,
)
from app.utils import check_org_access, get_descendant_organizations,require_superuser
from app.constants import OrgRoleEnum


def can_create_root_organization(company_id):
    """
    指定された会社にルート組織（parent_id=None）が既に存在するかどうかを確認
    """
    existing = Organization.query.filter_by(company_id=company_id, parent_id=None).first()
    return existing is None


def create_organization(user, name, org_code, company_id=None, parent_id=None):
    if not name or not org_code:
        raise ServiceValidationError("name と org_code は必須です")
     # --- ルート作成（superuser のみ許可） ---
    if parent_id is None:
        if not company_id:
            raise ServiceValidationError("ルート組織にはcompany_idが必須です。")
        # ★ superuser 以外は即 403
        if not require_superuser(user):
            raise ServicePermissionError("ルート組織作成の権限がありません。")
        
        if not can_create_root_organization(company_id):
            raise ServiceValidationError("この会社にはすでにルート組織が存在します")
        level = 1
    # --- 子作成（ORG_ADMIN 以上。SYSTEM_ADMIN は会社内なら可） ---
    else:
        parent = db.session.get(Organization, parent_id)
        if not parent:
            raise ServiceValidationError("指定された親組織が存在しません。")
        if company_id and company_id != parent.company_id:
            raise ServiceValidationError("指定されたcompany_idと親組織のcompany_idが一致しません。")
                # ORG_ADMIN: 自配下のみ / SYSTEM_ADMIN: 同一会社なら True / MEMBER: False
        if not check_org_access(user, parent.id, required_role=OrgRoleEnum.ORG_ADMIN):
            raise ServicePermissionError("この親組織配下に作成する権限がありません。")
        company_id = parent.company_id
        level = parent.level + 1

    # org_codeの重複チェック（同一会社内）
    existing = Organization.query.filter_by(company_id=company_id, org_code=org_code).first()
    if existing:
        raise ServiceValidationError("同一会社内でこの org_code は既に使用されています。")

    org = Organization(
        name=name,
        org_code=org_code,
        company_id=company_id,
        parent_id=parent_id,
        level=level
    )
    db.session.add(org)
    db.session.commit()
    return org



def get_organization_by_id(org_id):
    org = db.session.get(Organization, org_id)
    if not org:
        raise ServiceNotFoundError("organization not found")
    return org if org else None


def get_organizations(current_user, company_id=None):
    """
    ユーザーの権限に基づいてアクセス可能な組織一覧を返す
    """

    # ベースクエリ作成
    query = Organization.query
    if company_id:
        query = query.filter_by(company_id=company_id)
    
    # 全組織データ取得
    all_orgs = query.all()
    
    # ユーザーがアクセス可能な組織をフィルタリング
    accessible_orgs = _filter_organizations_by_access(current_user, all_orgs)
    
    return accessible_orgs


def update_organization(user, org_id, name=None, parent_id=None):
    if not check_org_access(user, org_id, required_role=OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError("組織を変更する権限がありません。")
    org = db.session.get(Organization, org_id)
    if not org:
        raise ServiceNotFoundError("organization not found")
    if name:
        org.name = name

    if parent_id == 0:
        parent_id = None

    if parent_id != org.parent_id:
        if parent_id is not None:
            parent = db.session.get(Organization, parent_id)
            if not parent:
                raise ServiceNotFoundError("指定された親組織が存在しません。")
            if not check_org_access(user, parent_id, required_role=OrgRoleEnum.ORG_ADMIN):
                raise ServicePermissionError("親組織を変更する権限がありません。")
            org.level = parent.level + 1
        else:
            if not require_superuser(user):
                raise ServicePermissionError("ルート組織作成の権限がありません。")
            org.level = 1
        org.parent_id = parent_id

    db.session.commit()
    return org


def delete_organization(user, org_id, force = False):

    org = db.session.get(Organization, org_id)
    if not org:
        raise ServiceNotFoundError("組織が存在しません。")
    if not check_org_access(user, org_id, required_role=OrgRoleEnum.ORG_ADMIN):
        raise ServicePermissionError("削除権限がありません。")

    #Forling key制約を考慮して、子組織やユーザーが存在する場合は削除できないようにする
    stmt = select(exists().where(Organization.parent_id == org_id))
    has_children = db.session.execute(stmt).scalar()
    if has_children:
        raise ServiceValidationError("子組織が存在するため削除できません。")
    stmt = select(exists().where(User.organization_id == org_id))
    has_user = db.session.execute(stmt).scalar()
    if has_user:
        raise ServiceValidationError("ユーザーが存在するため削除できません。")
    

    if force:
        try:
            db.session.delete(org)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ServiceValidationError(f'関連データがあるため削除に失敗しました: {e}')
        except Exception as e:
            db.session.rollback()
            raise ServiceValidationError(f'削除に失敗しました: {e}')
    else:
        org.soft_delete()
        db.session.commit()

    return True, "削除成功"


def get_organization_tree(current_user, company_id=None):
    """
    Organization.to_dict() を使ってツリー構造を再帰的に構築する
    ユーザーの権限と所属組織に基づいてフィルタリングを行う
    """
    # ベースクエリ作成
    orgs = Organization.query
    if company_id:
        orgs = orgs.filter_by(company_id=company_id)
    
    orgs = orgs.filter(Organization.is_deleted == False)
    # 全組織データ取得
    all_orgs = orgs.all()
    
    # ユーザーがアクセス可能な組織をフィルタリング
    accessible_orgs = _filter_organizations_by_access(current_user, all_orgs)
    
    if not accessible_orgs:
        return jsonify([])
    
    # 各 org を dict に変換し、children を追加
    org_map = {}
    for org in accessible_orgs:
        org_dict = org.to_dict()
        org_dict['children'] = []
        org_map[org.id] = org_dict

    # ツリー構造を作成
    root_nodes = []
    for org in org_map.values():
        parent_id = org['parent_id']
        if parent_id and parent_id in org_map:
            org_map[parent_id]['children'].append(org)
        else:
            root_nodes.append(org)

    return jsonify(root_nodes)


def get_children(parent_id):
    """
    指定された親組織IDに属する子組織を返す（モデルオブジェクト）
    """
    children = Organization.query.filter(Organization.parent_id == parent_id, Organization.is_deleted != True).all()
    return children


def _filter_organizations_by_access(user, all_orgs):
    """
    ユーザーの権限に基づいてアクセス可能な組織をフィルタリング
    """
    accessible_orgs = []
    
    # スーパーユーザーは全組織にアクセス可能
    if getattr(user, 'is_superuser', False):
        return all_orgs
    
    # SYSTEM_ADMIN権限をチェック
    system_admin_companies = _get_system_admin_companies(user)
    if system_admin_companies:
        # SYSTEM_ADMINの場合、同一会社の全組織にアクセス可能
        for org in all_orgs:
            if org.company_id in system_admin_companies:
                accessible_orgs.append(org)
        return accessible_orgs
    
    # ORG_ADMIN権限をチェック
    org_admin_orgs = _get_org_admin_accessible_orgs(user, all_orgs)
    if org_admin_orgs:
        accessible_orgs.extend(org_admin_orgs)
    
    # MEMBER権限：自組織のみ
    if user.organization_id:
        member_accessible = _get_member_accessible_orgs(user, all_orgs)
        accessible_orgs.extend(member_accessible)
    
    # 重複を除去
    return list(set(accessible_orgs))

def _get_system_admin_companies(user):
    """
    SYSTEM_ADMIN権限を持つ会社のIDリストを取得
    """
    company_ids = set()
    
    for scope in user.access_scopes:
        if scope.role == OrgRoleEnum.SYSTEM_ADMIN:
            # scope.organizationまたはscope.organization_idから会社IDを取得
            if scope.organization:
                company_ids.add(scope.organization.company_id)
            elif scope.organization_id:
                org = Organization.query.get(scope.organization_id)
                if org:
                    company_ids.add(org.company_id)
    
    return list(company_ids)

def _get_org_admin_accessible_orgs(user, all_orgs):
    """
    ORG_ADMIN権限でアクセス可能な組織リストを取得
    """
    accessible_orgs = []
    
    for scope in user.access_scopes:
        if scope.role == OrgRoleEnum.ORG_ADMIN:
            # 管理対象の組織IDを取得
            base_org_id = scope.organization_id or user.organization_id
            if base_org_id:
                # 自組織＋下位組織を取得
                descendant_orgs = get_descendant_organizations(base_org_id, all_orgs)
                accessible_orgs.extend(descendant_orgs)
    
    return accessible_orgs

def _get_member_accessible_orgs(user, all_orgs):
    """
    MEMBER権限でアクセス可能な組織リストを取得
    """
    accessible_orgs = []
    
    # 明示的にMEMBER権限が付与されている組織
    for scope in user.access_scopes:
        if scope.role == OrgRoleEnum.MEMBER and scope.organization_id:
            org = next((o for o in all_orgs if o.id == scope.organization_id), None)
            if org:
                accessible_orgs.append(org)
    
    # 所属組織（デフォルトのMEMBER権限）
    if user.organization_id:
        user_org = next((o for o in all_orgs if o.id == user.organization_id), None)
        if user_org:
            accessible_orgs.append(user_org)
    
    return accessible_orgs