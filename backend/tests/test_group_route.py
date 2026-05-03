import pytest


# =====================
# Group CRUD
# =====================

def test_create_group(system_admin_client):
    res = system_admin_client.post("/groups", json={
        "name": "TestGroup"
    })
    assert res.status_code == 201

    data = res.get_json()
    assert data["name"] == "TestGroup"
    assert "id" in data


def test_get_group(system_admin_client):
    # create
    res = system_admin_client.post("/groups", json={"name": "TestGroup"})
    group = res.get_json()

    # get
    res = system_admin_client.get(f"/groups/{group['id']}")
    assert res.status_code == 200

    data = res.get_json()
    assert data["id"] == group["id"]


def test_list_groups(system_admin_client):
    system_admin_client.post("/groups", json={"name": "Group1"})
    system_admin_client.post("/groups", json={"name": "Group2"})

    res = system_admin_client.get("/groups")
    assert res.status_code == 200

    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_update_group(system_admin_client):
    res = system_admin_client.post("/groups", json={"name": "OldName"})
    group = res.get_json()

    res = system_admin_client.patch(
        f"/groups/{group['id']}",
        json={"name": "NewName"}
    )
    assert res.status_code == 200

    data = res.get_json()
    assert data["name"] == "NewName"


def test_delete_group(system_admin_client):
    res = system_admin_client.post("/groups", json={"name": "DeleteMe"})
    group = res.get_json()

    res = system_admin_client.delete(f"/groups/{group['id']}")
    assert res.status_code == 204

    # 確認（取得できない）
    res = system_admin_client.get(f"/groups/{group['id']}")
    assert res.status_code in (404, 400)