import pytest
import datetime
from app.constants import StatusEnum


@pytest.fixture(scope="function")
def test_task_data():
    """テスト用のタスクデータを返す"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": "2024-12-31"
    }


@pytest.fixture(scope="function")
def task(system_admin_client, test_task_data):
    """エンドポイント経由でテスト用タスクを作成"""
    client = system_admin_client
    
    # タスクを作成
    res = client.post("/tasks", json=test_task_data)
    assert res.status_code == 201
    
    task_data = res.get_json()['task']
    task_data.update(test_task_data)  # 元のデータも含める
    return task_data


@pytest.fixture
def make_objective_data(task):
    def _make(title="test objective", due_date=None, assigned_user_id=None, status=None):
        data = {
            "title": title,
            "task_id": task["id"],
        }
        if due_date:
            data["due_date"] = due_date
        if assigned_user_id:
            data["assigned_user_id"] = assigned_user_id
        if status:
            data["status"] = status
        return data
    return _make


def validate_objective_response_data(objective_data, expected_title=None, expected_due_date=None, expected_assigned_user_id=None, expected_task_id=None):
    """Objectiveレスポンスデータのバリデーション"""
    # 必須フィールドの存在確認
    assert "id" in objective_data
    assert "title" in objective_data
    assert "task_id" in objective_data
    assert "status" in objective_data
    assert "created_at" in objective_data
    
    # データ型の確認
    assert isinstance(objective_data["id"], int)
    assert isinstance(objective_data["title"], str)
    assert isinstance(objective_data["task_id"], int)
    assert isinstance(objective_data["status"], str)
    assert objective_data["status"] in [status.name for status in StatusEnum]
    
    # 期待値との比較
    if expected_title:
        assert objective_data["title"] == expected_title
    if expected_due_date:
        assert objective_data["due_date"] == expected_due_date
    if expected_assigned_user_id:
        assert objective_data["assigned_user_id"] == expected_assigned_user_id
    if expected_task_id:
        assert objective_data["task_id"] == expected_task_id


def validate_objectives_list_response(objectives_data):
    """Objectives一覧レスポンスデータのバリデーション"""
    assert "objectives" in objectives_data
    assert isinstance(objectives_data["objectives"], list)
    
    for objective in objectives_data["objectives"]:
        validate_objective_response_data(objective)
        # 拡張フィールドの確認
        assert "assigned_user_name" in objective
        assert "latest_progress" in objective
        assert "latest_report_date" in objective


def assert_objective_deleted_via_endpoint(client, objective_id):
    """エンドポイント経由でObjectiveが削除されていることを確認"""
    resp = client.get(f"/objectives/{objective_id}")
    assert resp.status_code == 404


def assert_objective_exists_via_endpoint(client, objective_id, expected_data=None):
    """エンドポイント経由でObjectiveが存在することを確認"""
    resp = client.get(f"/objectives/{objective_id}")
    assert resp.status_code == 200
    
    objective_data = resp.get_json()
    validate_objective_response_data(objective_data)
    
    if expected_data:
        for key, expected_value in expected_data.items():
            assert objective_data.get(key) == expected_value
    
    return objective_data


class TestObjectivesAPI:
    @pytest.fixture(autouse=True)
    def setup(self, task_access_users, task, login_as_user, make_objective_data, setup_task_access):
        # full/edit/viewユーザーをセット
        self.users = task_access_users
        self.task = task
        self.make_objective_data = make_objective_data
        self.login_as_user = login_as_user
        setup_task_access(task)

    def test_get_objectives_for_task_view(self):
        """VIEW権限でタスクのObjective一覧取得テスト"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.get(f"/objectives/tasks/{self.task['id']}")
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        data = resp.get_json()
        validate_objectives_list_response(data)

    def test_create_objective_full(self):
        """FULL権限でObjective作成テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        test_title = "Test Objective for Full User"
        test_due_date = "2024-12-25"
        data = self.make_objective_data(
            title=test_title,
            due_date=test_due_date,
            assigned_user_id=user['id']
        )
        
        resp = client.post("/objectives", json=data)
        assert resp.status_code == 201
        
        # レスポンスデータのバリデーション
        response_data = resp.get_json()
        assert "message" in response_data
        assert "objective" in response_data
        
        objective = response_data["objective"]
        validate_objective_response_data(
            objective,
            expected_title=test_title,
            expected_due_date=test_due_date,
            expected_assigned_user_id=user['id'],
            expected_task_id=self.task['id']
        )
        
        # エンドポイント経由で正しく保存されているかを確認
        assert_objective_exists_via_endpoint(client, objective["id"], {
            "title": test_title,
            "due_date": test_due_date,
            "assigned_user_id": user['id'],
            "task_id": self.task['id']
        })

    def test_create_objective_edit(self):
        """EDIT権限でObjective作成テスト"""
        user = self.users['edit']
        client = self.login_as_user(user['email'], user['password'])
        
        test_title = "Test Objective for Edit User"
        data = self.make_objective_data(title=test_title)
        
        resp = client.post("/objectives", json=data)
        assert resp.status_code == 201
        
        # レスポンスデータのバリデーション
        response_data = resp.get_json()
        objective = response_data["objective"]
        validate_objective_response_data(
            objective,
            expected_title=test_title,
            expected_task_id=self.task['id']
        )
        
        # エンドポイント経由で作成確認
        assert_objective_exists_via_endpoint(client, objective["id"])

    def test_create_objective_view(self):
        """VIEW権限でObjective作成テスト（権限エラー）"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        data = self.make_objective_data()
        resp = client.post("/objectives", json=data)
        assert resp.status_code == 403

    def test_create_objective_validation_errors(self):
        """Objective作成時のバリデーションエラーテスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        # タイトルなし
        data = {"task_id": self.task['id']}
        resp = client.post("/objectives", json=data)
        assert resp.status_code in [400, 422]  # バリデーションエラー
        
        # タスクIDなし
        data = {"title": "Test Objective"}
        resp = client.post("/objectives", json=data)
        assert resp.status_code in [400, 422]  # バリデーションエラー
        
        # 不正な日付形式
        data = self.make_objective_data(due_date="invalid-date")
        resp = client.post("/objectives", json=data)
        assert resp.status_code in [400, 422]  # バリデーションエラー

    def test_update_objective_full(self, created_objective):
        """FULL権限でObjective更新テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        updated_title = "Updated Objective Title"
        updated_due_date = "2025-01-15"
        update_data = {
            "title": updated_title,
            "due_date": updated_due_date,
            "assigned_user_id": user['id']
        }
        
        resp = client.put(f"/objectives/{created_objective['id']}", json=update_data)
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        response_data = resp.get_json()
        assert "message" in response_data
        assert "objective" in response_data
        
        objective = response_data["objective"]
        validate_objective_response_data(
            objective,
            expected_title=updated_title,
            expected_due_date=updated_due_date,
            expected_assigned_user_id=user['id']
        )
        
        # エンドポイント経由で更新確認
        assert_objective_exists_via_endpoint(client, created_objective['id'], {
            "title": updated_title,
            "due_date": updated_due_date,
            "assigned_user_id": user['id']
        })

    def test_update_objective_edit(self, created_objective):
        """EDIT権限でObjective更新テスト"""
        user = self.users['edit']
        client = self.login_as_user(user['email'], user['password'])
        
        updated_title = "Updated by Edit User"
        resp = client.put(f"/objectives/{created_objective['id']}", json={"title": updated_title})
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        response_data = resp.get_json()
        objective = response_data["objective"]
        validate_objective_response_data(objective, expected_title=updated_title)
        
        # エンドポイント経由で更新確認
        assert_objective_exists_via_endpoint(client, created_objective['id'], {
            "title": updated_title
        })

    def test_update_objective_view(self, created_objective):
        """VIEW権限でObjective更新テスト（権限エラー）"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        resp = client.put(f"/objectives/{created_objective['id']}", json={"title": "updated"})
        assert resp.status_code == 403

    def test_delete_objective_full(self, created_objective):
        """FULL権限でObjective削除テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.delete(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        response_data = resp.get_json()
        assert "message" in response_data
        assert isinstance(response_data["message"], str)
        
        # エンドポイント経由で削除されたことを確認
        assert_objective_deleted_via_endpoint(client, created_objective['id'])

    def test_delete_objective_edit(self, created_objective):
        """EDIT権限でObjective削除テスト"""
        user = self.users['edit']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.delete(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 200
        
        # エンドポイント経由で削除されたことを確認
        assert_objective_deleted_via_endpoint(client, created_objective['id'])

    def test_delete_objective_view(self, created_objective):
        """VIEW権限でObjective削除テスト（権限エラー）"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        resp = client.delete(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 403

    def test_delete_objective_order_rebalancing(self):
        """Objective削除時の順序再調整テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        # 3つのObjectiveを作成
        objectives = []
        for i in range(3):
            data = self.make_objective_data(title=f"Objective {i+1}")
            resp = client.post("/objectives", json=data)
            assert resp.status_code == 201
            objectives.append(resp.get_json()["objective"])
        
        # 真ん中のObjectiveを削除
        middle_id = objectives[1]["id"]
        resp = client.delete(f"/objectives/{middle_id}")
        assert resp.status_code == 200
        
        # 削除されたObjectiveにアクセスできないことを確認
        assert_objective_deleted_via_endpoint(client, middle_id)
        
        # 残りのObjectiveが存在することを確認
        assert_objective_exists_via_endpoint(client, objectives[0]["id"])
        assert_objective_exists_via_endpoint(client, objectives[2]["id"])
        
        # タスクのObjective一覧を取得して順序を確認
        list_resp = client.get(f"/objectives/tasks/{self.task['id']}")
        assert list_resp.status_code == 200
        remaining_objectives = list_resp.get_json()["objectives"]
        
        # 2つのObjectiveが残っていることを確認
        assert len(remaining_objectives) == 2
        # IDが削除されていないObjectiveのものであることを確認
        remaining_ids = [obj["id"] for obj in remaining_objectives]
        assert objectives[0]["id"] in remaining_ids
        assert objectives[2]["id"] in remaining_ids
        assert middle_id not in remaining_ids

    def test_get_objective_detail_view(self, created_objective):
        """VIEW権限でObjective詳細取得テスト"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.get(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        objective_data = resp.get_json()
        validate_objective_response_data(objective_data)

    def test_get_objective_detail_edit(self, created_objective):
        """EDIT権限でObjective詳細取得テスト"""
        user = self.users['edit']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.get(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        objective_data = resp.get_json()
        validate_objective_response_data(objective_data)

    def test_get_objective_detail_full(self, created_objective):
        """FULL権限でObjective詳細取得テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.get(f"/objectives/{created_objective['id']}")
        assert resp.status_code == 200
        
        # レスポンスデータのバリデーション
        objective_data = resp.get_json()
        validate_objective_response_data(objective_data)

    def test_get_objective_not_found(self):
        """存在しないObjective取得テスト"""
        user = self.users['view']
        client = self.login_as_user(user['email'], user['password'])
        
        resp = client.get("/objectives/99999")
        assert resp.status_code == 404

    def test_get_objectives_extended_fields(self):
        """Objective一覧の拡張フィールドテスト"""
        user = self.users['edit']
        client = self.login_as_user(user['email'], user['password'])

        # Objective 作成（assigned_user_id に editユーザーを設定）
        data = self.make_objective_data(assigned_user_id=user['id'])
        resp = client.post("/objectives", json=data)
        assert resp.status_code == 201
        obj = resp.get_json()["objective"]
        obj_id = obj["id"]

        # Progress を1件追加（報告日付き）
        progress_data = {
            "detail": "latest progress content",
            "report_date": datetime.datetime.now().isoformat()
        }
        progress_resp = client.post(f"/updates/{obj_id}", json=progress_data)
        assert progress_resp.status_code == 201

        # 取得して拡張項目を確認
        get_resp = client.get(f"/objectives/tasks/{self.task['id']}")
        assert get_resp.status_code == 200
        
        # レスポンスデータのバリデーション
        objectives_data = get_resp.get_json()
        validate_objectives_list_response(objectives_data)
        
        objectives = objectives_data["objectives"]
        assert len(objectives) == 1

        obj = objectives[0]
        # 拡張フィールドの詳細確認
        assert obj["assigned_user_name"] == user["name"]
        assert obj["latest_progress"] == "latest progress content"
        assert "latest_report_date" in obj
        assert obj["latest_report_date"] is not None

    def test_create_objective_with_all_fields(self):
        """全フィールドを指定したObjective作成テスト"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        test_data = {
            "title": "Complete Objective Test",
            "task_id": self.task['id'],
            "due_date": "2024-12-31",
            "assigned_user_id": user['id']
        }
        
        resp = client.post("/objectives", json=test_data)
        assert resp.status_code == 201
        
        # レスポンスデータの詳細バリデーション
        response_data = resp.get_json()
        objective = response_data["objective"]
        
        validate_objective_response_data(
            objective,
            expected_title=test_data["title"],
            expected_due_date=test_data["due_date"],
            expected_assigned_user_id=test_data["assigned_user_id"],
            expected_task_id=test_data["task_id"]
        )
        
        # display_orderが正しく設定されているか確認（エンドポイント経由）
        detailed_objective = assert_objective_exists_via_endpoint(client, objective["id"])
        assert isinstance(detailed_objective.get("display_order"), (int, type(None)))


    def test_create_objective_with_status(self):
        """Objective作成時にステータス指定が反映されるかを確認"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        test_status = StatusEnum.IN_PROGRESS.name
        data = self.make_objective_data(status=test_status)
        
        resp = client.post("/objectives", json=data)
        assert resp.status_code == 201
        objective = resp.get_json()["objective"]
        
        assert objective["status"] == test_status

    def test_update_objective_status(self, created_objective):
        """Objectiveのステータスを更新できるかを確認"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        new_status = StatusEnum.COMPLETED.name
        resp = client.put(
            f"/objectives/{created_objective['id']}",
            json={"status": new_status}
        )
        assert resp.status_code == 200
        updated = resp.get_json()["objective"]
        assert updated["status"] == new_status
        
        # エンドポイント経由でも確認
        detailed = assert_objective_exists_via_endpoint(client, created_objective["id"])
        assert detailed["status"] == new_status

    def test_create_objective_invalid_status(self):
        """不正なステータス指定時のバリデーションエラー確認"""
        user = self.users['full']
        client = self.login_as_user(user['email'], user['password'])
        
        data = self.make_objective_data(status="INVALID_STATUS")
        resp = client.post("/objectives", json=data)
        assert resp.status_code in [400, 422]



@pytest.fixture
def created_objective(login_as_user, task_access_users, make_objective_data):
    """full権限でObjectiveを1件作成し、そのdictを返す"""
    user = task_access_users['full']
    client = login_as_user(user['email'], user['password'])
    data = make_objective_data()
    resp = client.post("/objectives", json=data)
    assert resp.status_code == 201
    obj_id = resp.get_json()['objective']["id"]
    return {"id": obj_id}