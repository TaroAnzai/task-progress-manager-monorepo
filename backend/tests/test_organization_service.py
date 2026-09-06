import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.constants import OrgRoleEnum
from app.models import AccessScope, Company, Organization, User
from app.service_errors import ServiceNotFoundError, ServicePermissionError, ServiceValidationError
from app.services import organization_service as service


def make_user(email, org=None, role=None, *, superuser=False):
    user = User(name=email, email=email, organization=org, is_superuser=superuser)
    db.session.add(user); db.session.flush()
    if role is not None:
        db.session.add(AccessScope(user_id=user.id, organization_id=org.id, role=role)); db.session.flush()
    return user


def make_child(root, code):
    org = Organization(name=code, org_code=code, company_id=root.company_id,
                       parent_id=root.id, level=root.level + 1)
    db.session.add(org); db.session.flush()
    return org


def test_create_root_validates_fields_permission_and_duplicate(root_org):
    root = db.session.get(Organization, root_org["id"])
    superuser = make_user("root-super@example.com", superuser=True)
    with pytest.raises(ServiceValidationError, match="必須"):
        service.create_organization(superuser, "", "code", root.company_id)
    with pytest.raises(ServiceValidationError, match="company_id"):
        service.create_organization(superuser, "Root", "code")
    member = make_user("root-member@example.com", root, OrgRoleEnum.MEMBER)
    with pytest.raises(ServicePermissionError):
        service.create_organization(member, "Other", "other", root.company_id)
    with pytest.raises(ServiceValidationError, match="すでにルート"):
        service.create_organization(superuser, "Other", "other", root.company_id)


def test_create_child_validates_parent_company_permission_and_code(root_org, test_other_company):
    root = db.session.get(Organization, root_org["id"])
    member = make_user("child-member@example.com", root, OrgRoleEnum.MEMBER)
    with pytest.raises(ServiceValidationError, match="親組織"):
        service.create_organization(member, "Child", "c", parent_id=999999)
    with pytest.raises(ServiceValidationError, match="一致"):
        service.create_organization(member, "Child", "c", test_other_company["id"], root.id)
    with pytest.raises(ServicePermissionError):
        service.create_organization(member, "Child", "c", parent_id=root.id)
    admin = make_user("child-admin@example.com", root, OrgRoleEnum.ORG_ADMIN)
    with pytest.raises(ServiceValidationError, match="org_code"):
        service.create_organization(admin, "Duplicate", root.org_code, parent_id=root.id)
    child = service.create_organization(admin, "Child", "created-child", parent_id=root.id)
    assert (child.company_id, child.parent_id, child.level) == (root.company_id, root.id, root.level + 1)


def test_get_and_update_not_found_and_permission(root_org):
    root = db.session.get(Organization, root_org["id"])
    with pytest.raises(ServiceNotFoundError): service.get_organization_by_id(999999)
    member = make_user("update-member@example.com", root, OrgRoleEnum.MEMBER)
    with pytest.raises(ServicePermissionError): service.update_organization(member, root.id, name="No")
    superuser = make_user("update-super@example.com", superuser=True)
    with pytest.raises(ServiceNotFoundError): service.update_organization(superuser, 999999, name="Missing")


def test_update_moves_and_roots_organization(root_org):
    root = db.session.get(Organization, root_org["id"])
    parent, target = make_child(root, "move-parent"), make_child(root, "move-target")
    superuser = make_user("move-super@example.com", superuser=True)
    moved = service.update_organization(superuser, target.id, name="Moved", parent_id=parent.id)
    assert (moved.name, moved.parent_id, moved.level) == ("Moved", parent.id, parent.level + 1)
    rooted = service.update_organization(superuser, target.id, parent_id=0)
    assert rooted.parent_id is None and rooted.level == 1


def test_update_parent_errors(root_org, test_other_company):
    root = db.session.get(Organization, root_org["id"])
    target = make_child(root, "parent-target")
    admin = make_user("parent-admin@example.com", root, OrgRoleEnum.ORG_ADMIN)
    with pytest.raises(ServiceNotFoundError, match="親組織"):
        service.update_organization(admin, target.id, parent_id=999999)
    with pytest.raises(ServicePermissionError, match="ルート"):
        service.update_organization(admin, target.id, parent_id=0)
    other = Organization(name="Other", org_code="other-parent", company_id=test_other_company["id"], level=1)
    db.session.add(other); db.session.flush()
    with pytest.raises(ServicePermissionError, match="親組織"):
        service.update_organization(admin, target.id, parent_id=other.id)


def test_delete_errors_force_and_rollback(monkeypatch, root_org):
    root = db.session.get(Organization, root_org["id"])
    superuser = make_user("delete-super@example.com", superuser=True)
    with pytest.raises(ServiceNotFoundError): service.delete_organization(superuser, 999999)
    member = make_user("delete-member@example.com", root, OrgRoleEnum.MEMBER)
    empty = make_child(root, "empty-forbidden")
    with pytest.raises(ServicePermissionError): service.delete_organization(member, empty.id)
    with pytest.raises(ServiceValidationError, match="子組織"):
        service.delete_organization(superuser, root.id)
    occupied = Organization(name="Occupied", org_code="occupied", company_id=root.company_id, level=1)
    db.session.add(occupied); db.session.flush()
    make_user("occupied-user@example.com", occupied)
    with pytest.raises(ServiceValidationError, match="ユーザー"):
        service.delete_organization(superuser, occupied.id)
    target = make_child(root, "force-empty")
    target_id = target.id
    assert service.delete_organization(superuser, target_id, force=True) == (True, "削除成功")
    assert db.session.get(Organization, target_id) is None
    rollback_target = make_child(root, "rollback-empty")
    monkeypatch.setattr(db.session, "commit", lambda: (_ for _ in ()).throw(IntegrityError("x", {}, None)))
    with pytest.raises(ServiceValidationError, match="関連データ"):
        service.delete_organization(superuser, rollback_target.id, force=True)


def test_tree_and_access_filters_cover_role_behaviors(root_org):
    root = db.session.get(Organization, root_org["id"])
    child = make_child(root, "tree-child")
    superuser = make_user("tree-super@example.com", superuser=True)
    payload = service.get_organization_tree(superuser, root.company_id).get_json()
    assert next(x for x in payload if x["id"] == root.id)["children"][0]["id"] == child.id
    company = Company(name="Empty company"); db.session.add(company); db.session.flush()
    assert service.get_organization_tree(superuser, company.id).get_json() == []
    member = make_user("filter-member@example.com", root, OrgRoleEnum.MEMBER)
    assert set(service._filter_organizations_by_access(member, [root, child])) == {root}
    admin = make_user("filter-admin@example.com", root, OrgRoleEnum.ORG_ADMIN)
    assert set(service._filter_organizations_by_access(admin, [root, child])) == {root, child}
    system = make_user("filter-system@example.com", root, OrgRoleEnum.SYSTEM_ADMIN)
    assert set(service._filter_organizations_by_access(system, [root, child])) == {root, child}
