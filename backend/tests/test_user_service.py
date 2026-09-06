from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.constants import OrgRoleEnum
from app.models import AccessScope, Organization, Task, User
from app.service_errors import ServiceNotFoundError, ServicePermissionError, ServiceValidationError
from app.services import user_service


def make_user(email, org=None, role=None, *, superuser=False, wp_id=None):
    user = User(name=email.split("@")[0], email=email, organization=org,
                is_superuser=superuser, wp_user_id=wp_id)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()
    if role is not None:
        db.session.add(AccessScope(user_id=user.id, organization_id=org.id, role=role))
        db.session.flush()
    return user


def test_create_user_rejects_missing_actor_org_and_permission(root_org):
    with pytest.raises(ServiceNotFoundError):
        user_service.create_user({}, None)
    actor = User(name="actor", email="actor-create@example.com", is_superuser=True)
    with pytest.raises(ServiceValidationError, match="organization_id"):
        user_service.create_user({}, actor)
    org = db.session.get(Organization, root_org["id"])
    member = make_user("member-create@example.com", org, OrgRoleEnum.MEMBER)
    with pytest.raises(ServicePermissionError):
        user_service.create_user({"organization_id": org.id}, member)


@pytest.mark.parametrize(("overrides", "message"), [
    ({"email": "invalid"}, "メールアドレス"),
    ({"role": "OWNER"}, "role"),
    ({"organization_id": 999999}, "組織ID"),
])
def test_create_user_validates_inputs(superuser, root_org, overrides, message):
    data = {"name": "Created", "email": "created-service@example.com",
            "password": "secret", "organization_id": root_org["id"]}
    data.update(overrides)
    with pytest.raises(ServiceValidationError, match=message):
        user_service.create_user(data, db.session.get(User, superuser["id"]))


def test_create_user_rejects_duplicate_wp_id(superuser, root_org):
    org = db.session.get(Organization, root_org["id"])
    make_user("existing-wp@example.com", org, wp_id=42)
    with pytest.raises(ServiceValidationError, match="wp_user_id"):
        user_service.create_user({"name": "Duplicate", "email": "new-wp@example.com",
            "password": "secret", "organization_id": org.id, "wp_user_id": 42},
            db.session.get(User, superuser["id"]))


def test_update_user_updates_all_fields(superuser, root_org):
    actor = db.session.get(User, superuser["id"])
    root = db.session.get(Organization, root_org["id"])
    destination = Organization(name="Destination", org_code="destination",
        company_id=root.company_id, level=1)
    db.session.add(destination)
    db.session.flush()
    target = make_user("before-update@example.com", root, wp_id=10)
    result = user_service.update_user(target.id, {"organization_id": destination.id,
        "name": "After", "wp_user_id": 11, "email": " After@Example.com ",
        "password": "new-password"}, actor)
    assert (result.organization_id, result.name, result.wp_user_id) == (destination.id, "After", 11)
    assert result.email == "After@Example.com"
    assert result.normalized_email == "after@example.com"
    assert result.check_password("new-password")


def test_update_user_not_found_no_org_and_permission(superuser, root_org):
    actor = db.session.get(User, superuser["id"])
    with pytest.raises(ServiceNotFoundError):
        user_service.update_user(999999, {}, actor)
    orphan = make_user("orphan-update@example.com")
    with pytest.raises(ServicePermissionError):
        user_service.update_user(orphan.id, {}, actor)
    org = db.session.get(Organization, root_org["id"])
    member = make_user("member-update@example.com", org, OrgRoleEnum.MEMBER)
    target = make_user("target-update@example.com", org)
    with pytest.raises(ServicePermissionError):
        user_service.update_user(target.id, {"name": "nope"}, member)
    with pytest.raises(ServiceValidationError, match="組織ID"):
        user_service.update_user(target.id, {"organization_id": 999999}, actor)


@pytest.mark.parametrize(("field", "value", "message"), [
    ("wp_user_id", 77, "wp_user_id"),
    ("email", "duplicate-update@example.com", "メールアドレス"),
    ("email", "bad-email", "メールアドレス形式"),
])
def test_update_user_rejects_duplicate_and_invalid_values(superuser, root_org, field, value, message):
    actor = db.session.get(User, superuser["id"])
    org = db.session.get(Organization, root_org["id"])
    make_user("duplicate-update@example.com", org, wp_id=77)
    target = make_user("target-identifiers@example.com", org, wp_id=78)
    with pytest.raises(ServiceValidationError, match=message):
        user_service.update_user(target.id, {field: value}, actor)


def test_get_user_by_id_enforces_company_boundary(root_org, other_root_org):
    actor = make_user("actor-company@example.com", db.session.get(Organization, root_org["id"]))
    target = make_user("target-company@example.com", db.session.get(Organization, other_root_org["id"]))
    with pytest.raises(ServicePermissionError):
        user_service.get_user_by_id(target.id, actor)
    with pytest.raises(ServiceNotFoundError):
        user_service.get_user_by_id(999999, actor)


def test_force_delete_removes_user_and_scope(superuser, root_org):
    actor = db.session.get(User, superuser["id"])
    target = make_user("force-delete@example.com", db.session.get(Organization, root_org["id"]), OrgRoleEnum.MEMBER)
    target_id = target.id
    assert "関連スコープ" in user_service.delete_user(target_id, actor, force=True)["message"]
    assert db.session.get(User, target_id) is None
    assert AccessScope.query.filter_by(user_id=target_id).count() == 0


def test_force_delete_refuses_related_task(superuser, root_org):
    actor = db.session.get(User, superuser["id"])
    org = db.session.get(Organization, root_org["id"])
    target = make_user("related-delete@example.com", org)
    db.session.add(Task(title="owned", created_by=target.id, organization_id=org.id))
    db.session.flush()
    with pytest.raises(ServiceValidationError, match="関連するタスク"):
        user_service.delete_user(target.id, actor, force=True)


def test_delete_errors_and_integrity_rollback(monkeypatch, superuser, root_org):
    actor = db.session.get(User, superuser["id"])
    org = db.session.get(Organization, root_org["id"])
    with pytest.raises(ServiceNotFoundError):
        user_service.delete_user(999999, actor)
    member = make_user("member-delete@example.com", org, OrgRoleEnum.MEMBER)
    target = make_user("target-delete@example.com", org)
    with pytest.raises(ServicePermissionError):
        user_service.delete_user(target.id, member)
    monkeypatch.setattr(user_service, "can_delete_user", lambda _: True)
    monkeypatch.setattr(db.session, "commit", lambda: (_ for _ in ()).throw(IntegrityError("x", {}, None)))
    with pytest.raises(ServiceValidationError, match="関連データ"):
        user_service.delete_user(target.id, actor, force=True)


def test_lookup_helpers_cover_errors_and_tree_failure(monkeypatch, root_org):
    org = db.session.get(Organization, root_org["id"])
    member = make_user("lookup-member@example.com", org, OrgRoleEnum.MEMBER)
    target = make_user("lookup-target@example.com", org, wp_id=321)
    for call in (lambda: user_service.get_user_by_email(target.email, member),
                 lambda: user_service.get_user_by_wp_user_id(321, member)):
        with pytest.raises(ServicePermissionError): call()
    for call in (lambda: user_service.get_user_by_email("missing@example.com", member),
                 lambda: user_service.get_user_by_wp_user_id(999999, member)):
        with pytest.raises(ServiceNotFoundError): call()
    with pytest.raises(ServicePermissionError):
        user_service.get_users_by_org_tree(org.id, member)
    member.is_superuser = True
    monkeypatch.setattr(user_service, "get_all_child_organizations", lambda _: (_ for _ in ()).throw(RuntimeError("tree failed")))
    with pytest.raises(ServiceValidationError, match="tree failed"):
        user_service.get_users_by_org_tree(org.id, member)


def test_list_helpers_return_empty_for_stale_requester(root_org):
    stale = SimpleNamespace(id=999999, organization_id=root_org["id"])
    assert user_service.get_users(stale) == []
    assert user_service.get_user_for_admin(stale, {}) == []
