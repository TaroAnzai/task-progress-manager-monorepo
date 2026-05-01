import uuid

import pytest

from tests.utils import check_response_message

@pytest.fixture(scope="function")
def order_user(system_admin_client, root_org):
    email = f"order_user_{uuid.uuid4()}@example.com"
    payload = {
        "name": "OrderUser",
        "email": email,
        "password": "testpass",
        "organization_id": root_org["id"],
        "role": "MEMBER"
    }
    res = system_admin_client.post("/users", json=payload)
    assert res.status_code == 201
    resUser = res.get_json()["user"]
    user = payload
    user["password"] = "testpass"
    user["id"] = resUser["id"]
    return user

@pytest.fixture(scope="function")
def order_user_client(order_user, login_as_user):
    return login_as_user(order_user["email"], order_user["password"])

@pytest.fixture(scope="function")
def order_user_tasks(order_user_client):
    tasks = []
    for i in range(3):
        res = order_user_client.post("/tasks", json={"title": f"Order Task {i+1}"})
        assert res.status_code == 201
        tasks.append(res.get_json()["task"])
    return tasks

class TestTaskOrderRoutes:
    def test_get_task_order(self, order_user_client, order_user_tasks, order_user):
        user_id = order_user["id"]
        res = order_user_client.get(f"/task_orders?user_id={user_id}")
        print(res.get_json())
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert len(data) == len(order_user_tasks)
        expected_order = [t["id"] for t in reversed(order_user_tasks)]
        returned_order = [item["task_id"] for item in data]
        assert returned_order == expected_order

    def test_save_task_order_and_get(self, order_user_client, order_user_tasks, order_user):
        user_id = order_user["id"]
        new_order = [t["id"] for t in order_user_tasks]
        res = order_user_client.post(f"/task_orders", json={"task_ids": new_order, "user_id": user_id})
        assert res.status_code == 200
        assert res.get_json()["message"] == "タスクの並び順を保存しました"
        res = order_user_client.get(f"/task_orders?user_id={user_id}")
        assert res.status_code == 200
        after_order = [item["task_id"] for item in res.get_json()]
        assert after_order == new_order

    def test_save_task_order_invalid(self, order_user_client, order_user):
        user_id = order_user["id"]
        res = order_user_client.post(f"/task_orders", json={"task_ids": "invalid", "user_id": user_id})
        assert res.status_code == 422
        assert check_response_message("Not a valid list.", res.get_json(), "task_ids")

    def test_task_order_requires_login(self, client, order_user):
        client.delete("/sessions/current")
        res = client.get(f"/task_orders?user_id={order_user['id']}")
        assert res.status_code == 401

    def test_save_task_order_post_requires_login(self, client, order_user, order_user_tasks):
        client.delete("/sessions/current")
        user_id = order_user["id"]
        res = client.post(f"/task_orders", json={"task_ids": [t["id"] for t in order_user_tasks], "user_id": user_id})
        assert res.status_code == 401

