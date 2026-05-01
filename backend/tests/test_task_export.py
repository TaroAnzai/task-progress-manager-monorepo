import pytest


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
def created_objective(client, created_task):
    """エンドポイント経由でテスト用オブジェクティブを作成"""
    objective_data = {
        "task_id": created_task["id"],
        "title": "Test Objective",
        "due_date": "2024-12-25"
    }
    
    res = client.post("/objectives", json=objective_data)
    assert res.status_code == 201
    
    objective_result = res.get_json()
    objective_result.update(objective_data)
    return objective_result


def test_task_export(system_admin_client, created_objective):
        client = system_admin_client
        res = client.get("/exports/excel")
        print("Response",res.get_json())
        assert res.status_code == 200

        
    