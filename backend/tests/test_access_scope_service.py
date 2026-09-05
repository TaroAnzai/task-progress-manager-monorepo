import pytest

from app.constants import OrgRoleEnum
from app.models import AccessScope, Organization, User, db
from app.service_errors import ServiceNotFoundError, ServiceValidationError
from app.services.access_scope_service import add_access_scope_to_user, delete_access_scope, get_user_scopes


def test_access_scope_lifecycle(app, test_company):
    user = User(name="Scope User", email="scope@example.com")
    org = Organization(name="Scope Org", org_code="scope", company_id=test_company["id"])
    db.session.add_all([user, org])
    db.session.flush()
    assert get_user_scopes(user.id) == []
    assert add_access_scope_to_user(user.id, {"organization_id": org.id, "role": OrgRoleEnum.MEMBER})["message"] == "アクセススコープを追加しました"
    scope = AccessScope.query.filter_by(user_id=user.id, organization_id=org.id).one()
    assert scope.role == OrgRoleEnum.MEMBER
    assert "すでに" in add_access_scope_to_user(user.id, {"organization_id": org.id, "role": OrgRoleEnum.MEMBER})["message"]
    assert "更新" in add_access_scope_to_user(user.id, {"organization_id": org.id, "role": OrgRoleEnum.ORG_ADMIN})["message"]
    assert scope.role == OrgRoleEnum.ORG_ADMIN
    assert get_user_scopes(user.id) == [scope]
    assert "削除" in delete_access_scope(scope.id)["message"]
    assert db.session.get(AccessScope, scope.id) is None


@pytest.mark.parametrize("operation", [get_user_scopes, lambda user_id: add_access_scope_to_user(user_id, {})])
def test_access_scope_operations_reject_unknown_user(operation):
    with pytest.raises(ServiceNotFoundError, match="ユーザー"):
        operation(999999)


@pytest.mark.parametrize("data", [{}, {"organization_id": 1}, {"role": OrgRoleEnum.MEMBER}])
def test_add_access_scope_requires_organization_and_role(app, data):
    user = User(name="Scope User", email=f"required-{len(data)}@example.com")
    db.session.add(user)
    db.session.flush()
    with pytest.raises(ServiceValidationError, match="必須"):
        add_access_scope_to_user(user.id, data)


def test_add_access_scope_rejects_invalid_role(app, root_org):
    user = User(name="Scope User", email="bad-role@example.com")
    db.session.add(user)
    db.session.flush()
    with pytest.raises(ServiceValidationError, match="無効な role"):
        add_access_scope_to_user(user.id, {"organization_id": root_org["id"], "role": "NOPE"})


def test_delete_access_scope_rejects_unknown_scope():
    with pytest.raises(ServiceNotFoundError, match="スコープ"):
        delete_access_scope(999999)
