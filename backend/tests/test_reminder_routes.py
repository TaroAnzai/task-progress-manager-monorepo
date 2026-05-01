# tests/test_reminder_routes.py
import pytest

# ルートは @login_required のため、client ではなく system_admin_client を使う
# conftest.py の system_admin_client はログイン済みクライアントを返す

def _fake_setting(**overrides):
    base = {
        "id": 123,
        "objective_id": 10,
        "condition_type": "NO_UPDATE",
        "threshold_days": 7,
        "frequency_type": "ONCE",
        "interval_days": None,
        "send_time_local": "09:00:00",
        "is_active": True,
        "last_sent_at": None,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    base.update(overrides)
    return base
@pytest.fixture(scope="function")
def test_task_data():
    """テスト用のタスクデータを返す"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": "2024-12-31"
    }


@pytest.fixture(scope="function")
def created_task(system_admin_client, test_task_data):
    client = system_admin_client
    """エンドポイント経由でテスト用タスクを作成"""
    
    # タスクを作成
    res = client.post("/tasks", json=test_task_data)
    assert res.status_code == 201
    
    task_data = res.get_json()['task']
    task_data.update(test_task_data)  # 元のデータも含める
    return task_data


@pytest.fixture(scope="function")
def created_objective(system_admin_client, created_task):
    client = system_admin_client
    """エンドポイント経由でテスト用オブジェクティブを作成"""
    objective_data = {
        "task_id": created_task["id"],
        "title": "Test Objective",
        "due_date": "2024-12-25"
    }
    
    res = client.post("/objectives", json=objective_data)
    assert res.status_code == 201
    
    objective_result = res.get_json()['objective']
    objective_result.update(objective_data)
    return objective_result

def test_create_reminder_success(created_objective, system_admin_client):
    objective = created_objective
    objective_id = objective['id']

    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    print(res.get_json())
    assert res.status_code == 201
    data = res.get_json()
    assert data["objective_id"] == objective_id
    assert data["condition_type"] == "NO_UPDATE"
    assert data["threshold_days"] == 3
    # 送信時刻は "HH:MM:SS" で返ってくる（ダミー想定）
    assert data["send_time_local"].startswith("09:00")


def test_create_reminder_validation_error(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']
    payload = {
        "condition_type": "NO_UPDATE",
        # threshold_days をあえて欠落
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    # with_common_error_responses による 400 マッピングを期待
    assert res.status_code == 400
    body = res.get_json()
    assert "threshold_days" in (body.get("message", "") or str(body))


def test_list_reminders_success(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']

    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res = system_admin_client.get(f"/objectives/{objective_id}/reminders")
    assert res.status_code == 200
    data = res.get_json()
    assert data["items"][0]["condition_type"] == "NO_UPDATE"


def test_get_reminder_success(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']

    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    id = res_data["id"]
    res = system_admin_client.get(f"/objectives/{id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == res_data["id"]


def test_update_reminder_success(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']

    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    id = res_data["id"]
    payload = {
        "condition_type": "NO_UPDATE",
        "frequency_type": "INTERVAL",
        "interval_days": 2,
        "send_time_local": "18:00",
        "threshold_days": 5,
    }
    res = system_admin_client.patch(f"/reminders/{id}", json=payload)
    print(res.get_json())
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == id
    assert data["frequency_type"] == "INTERVAL"
    assert data["interval_days"] == 2
    assert data["send_time_local"].startswith("18:00")


def test_delete_reminder_success(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']

    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    id = res_data["id"]
    res = system_admin_client.delete(f"/reminders/{id}")
    assert res.status_code == 204
    # 204 はボディ無しが基本
    assert not res.data


def test_permission_denied_mapping(system_admin_client,task_access_users,login_as_user, created_objective,):
    objective = created_objective
    objective_id = objective['id']
    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    client = system_admin_client

    res = client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    id = res_data["id"]

    # 他の組織のユーザーでアクセス
    client = login_as_user(
        task_access_users["full"]["email"],
        task_access_users["full"]["password"]
    )
    res = client.get(f"/reminders/{id}")
    # with_common_error_responses の想定: 403
    assert res.status_code in (401, 403)
    # 401 になる構成もあるため併記。通常は 403 を期待。


def test_not_found_mapping(system_admin_client):

    res = system_admin_client.get("/reminders/404")
    assert res.status_code == 404

def test_update_reminder(system_admin_client, created_objective):
    objective = created_objective
    objective_id = objective['id']
    #Make a reminder first
    payload = {
        "condition_type": "NO_UPDATE",
        "threshold_days": 3,
        "frequency_type": "ONCE",
        "send_time_local": "09:00",
        "is_active": True,
    }
    res = system_admin_client.post(f"/objectives/{objective_id}/reminders", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    id = res_data["id"]
    #Now update it
    payload = {
        "condition_type": "OVERDUE",
        "threshold_days": 1,
        "frequency_type": "INTERVAL",
        "interval_days": 2,
        "send_time_local": "10:00",
        "is_active": False,
    }
    res = system_admin_client.patch(f"/reminders/{id}", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == id
    assert data["condition_type"] == "OVERDUE"
    assert data["threshold_days"] == 1
    assert data["frequency_type"] == "INTERVAL"
    assert data["interval_days"] == 2
    assert data["send_time_local"].startswith("10:00")
    assert data["is_active"] is False

