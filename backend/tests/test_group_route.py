from typing import Any

from flask.testing import FlaskClient
import pytest

@pytest.fixture
def group_payload(root_org:dict[str, int|str], system_related_users: dict[str, dict[str, int|str]]):
    return {
            "name": "TestGroup",
            "scope_type": "ORGANIZATION",
            "organization_id": root_org["id"],
            "member_user_ids": [user["id"] for user in system_related_users.values()]
        }
@pytest.fixture
def group_payload2(root_org:dict[str, int|str], system_related_users: dict[str, dict[str, int|str]]):
    return {
            "name": "TestGroup2",
            "scope_type": "ORGANIZATION",
            "organization_id": root_org["id"],
            "member_user_ids": [user["id"] for user in system_related_users.values()]
        }

# =====================
# Group CRUD
# =====================

def test_create_group(system_admin_client:FlaskClient, group_payload:dict[str, Any]):
    res = system_admin_client.post("/groups", json=group_payload)
    assert res.status_code == 201, res.get_data(as_text=True)

    data = res.get_json()
    assert data["name"] == "TestGroup"
    assert "id" in data


def test_get_group(system_admin_client:FlaskClient, group_payload:dict[str, Any]):
    # create
    res = system_admin_client.post("/groups", json=group_payload)
    group = res.get_json()

    # get
    res = system_admin_client.get(f"/groups/{group['id']}")
    assert res.status_code == 200, res.get_data(as_text=True)

    data = res.get_json()
    assert data["id"] == group["id"]


def test_list_groups(system_admin_client:FlaskClient, group_payload:dict[str, Any], group_payload2:dict[str, Any]):
    system_admin_client.post("/groups", json=group_payload)
    system_admin_client.post("/groups", json=group_payload2)

    res = system_admin_client.get("/groups")
    assert res.status_code == 200, res.get_data(as_text=True)

    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_update_group(system_admin_client:FlaskClient, group_payload:dict[str, Any]):
    res = system_admin_client.post("/groups", json=group_payload)
    group = res.get_json()

    res = system_admin_client.patch(
        f"/groups/{group['id']}",
        json={"name": "NewName"}
    )
    assert res.status_code == 200, res.get_data(as_text=True)

    data = res.get_json()
    assert data["name"] == "NewName"


def test_delete_group(system_admin_client:FlaskClient, group_payload:dict[str, Any]):
    res = system_admin_client.post("/groups", json=group_payload)
    group = res.get_json()

    res = system_admin_client.delete(f"/groups/{group['id']}")
    assert res.status_code == 204, res.get_data(as_text=True)

    # 確認（取得できない）
    res = system_admin_client.get(f"/groups/{group['id']}")
    assert res.status_code in (404, 400), res.get_data(as_text=True)