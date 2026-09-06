import pytest

from app import db
from app.models import Group, GroupMember, GroupScopeType, Organization, User
from app.service_errors import ServicePermissionError, ServiceValidationError
from app.services import group_member_service as service


def user(email, org=None, *, superuser=False):
    value = User(name=email, email=email, organization=org, is_superuser=superuser)
    db.session.add(value); db.session.flush(); return value


def group(owner, scope, org=None):
    value = Group(name=f"{scope.name} group", owner_user_id=owner.id,
                  scope_type=scope, organization_id=org.id if org else None)
    db.session.add(value); db.session.flush(); return value


def test_get_members_not_found_and_private_permission(root_org):
    org = db.session.get(Organization, root_org["id"])
    owner, outsider = user("group-owner@example.com", org), user("group-outsider@example.com", org)
    private = group(owner, GroupScopeType.PRIVATE, org)
    with pytest.raises(ServiceValidationError, match="not found"):
        service.get_group_members(db.session, 999999, owner)
    with pytest.raises(ServicePermissionError):
        service.get_group_members(db.session, private.id, outsider)
    assert service.get_group_members(db.session, private.id, owner)["users"] == []


def test_group_visibility_superuser_global_and_organization(root_org, other_root_org):
    org = db.session.get(Organization, root_org["id"])
    other = db.session.get(Organization, other_root_org["id"])
    owner = user("visibility-owner@example.com", org)
    same, foreign = user("visibility-same@example.com", org), user("visibility-foreign@example.com", other)
    orphan, superuser = user("visibility-orphan@example.com"), user("visibility-super@example.com", superuser=True)
    global_group = group(owner, GroupScopeType.GLOBAL, org)
    assert service._can_view_group(superuser, global_group, org.company_id)
    assert service._can_view_group(same, global_group, org.company_id)
    assert not service._can_view_group(foreign, global_group, org.company_id)
    assert not service._can_view_group(orphan, global_group, org.company_id)
    org_group = group(owner, GroupScopeType.ORGANIZATION, org)
    assert service._can_view_group(same, org_group, org.company_id)
    assert not service._can_view_group(orphan, org_group, org.company_id)


def test_replace_members_validates_and_applies_exact_set(root_org):
    org = db.session.get(Organization, root_org["id"])
    owner = user("replace-owner@example.com", org)
    first, second = user("replace-first@example.com", org), user("replace-second@example.com", org)
    value = group(owner, GroupScopeType.PRIVATE, org)
    db.session.add(GroupMember(group_id=value.id, user_id=first.id)); db.session.commit()
    with pytest.raises(ServiceValidationError, match="not found"):
        service.replace_group_members(db.session, 999999, [], owner)
    with pytest.raises(ServicePermissionError):
        service.replace_group_members(db.session, value.id, [], first)
    with pytest.raises(ServiceValidationError, match="do not exist"):
        service.replace_group_members(db.session, value.id, [first.id, 999999], owner)
    response = service.replace_group_members(db.session, value.id, [second.id, second.id], owner)
    assert response["user_ids"] == [second.id]
    assert [(m.group_id, m.user_id) for m in GroupMember.query.all()] == [(value.id, second.id)]
    assert response["users"][0]["organization_name"] == org.name
