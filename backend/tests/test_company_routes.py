import pytest
from app import db
from app.models import Company

@pytest.fixture
def create_company_data():
    return {"name": "Test Company"}

def test_create_company(superuser_login, create_company_data):
    response = superuser_login.post("/companies", json=create_company_data)
    assert response.status_code == 201
    assert response.json["name"] == create_company_data["name"]



def test_list_companies(superuser_login, create_company_data):
    # 会社を作成
    response = superuser_login.post("/companies", json=create_company_data)
    assert response.status_code == 201
    response = superuser_login.get("/companies")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_company_by_id(superuser_login):
    # 会社作成
    post_response = superuser_login.post("/companies", json={"name": "by_id"})
    assert post_response.status_code == 201
    company_id = post_response.json["id"]

    # 取得
    get_response = superuser_login.get(f"/companies/{company_id}")
    assert get_response.status_code == 200
    assert get_response.json["id"] == company_id

def test_update_company(superuser_login):
    # 作成
    post_response = superuser_login.post("/companies", json={"name": "Old Name"})
    company_id = post_response.json["id"]

    # 更新
    response = superuser_login.put(f"/companies/{company_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json["name"] == "New Name"

def test_delete_and_restore_company(superuser_login):
    # 作成
    post_response = superuser_login.post("/companies", json={"name": "Delete Me"})
    company_id = post_response.json["id"]

    # 論理削除
    delete_response = superuser_login.delete(f"/companies/{company_id}")
    assert delete_response.status_code == 200

    # 通常取得で見えない
    get_response = superuser_login.get(f"/companies/{company_id}")
    assert get_response.status_code == 404

    # 削除済も含む取得で確認
    with_deleted = superuser_login.get(f"/companies/{company_id}?with_deleted=true")
    assert with_deleted.status_code == 200

    # 復元
    restore = superuser_login.post(f"/companies/{company_id}/restore")
    assert restore.status_code == 200

    # 復元後は通常取得で見える
    restored_get = superuser_login.get(f"/companies/{company_id}")
    assert restored_get.status_code == 200

def test_permanent_delete_company(superuser_login):
    # 作成
    post_response = superuser_login.post("/companies", json={"name": "Permanent Delete"})
    company_id = post_response.json["id"]

    # 物理削除
    response = superuser_login.delete(f"/companies/{company_id}?force=true")
    assert response.status_code == 200

    # with_deleted でも見えない
    get_response = superuser_login.get(f"/companies/with_deleted/{company_id}")
    assert get_response.status_code == 404
def test_company_duplicate_and_restore_logic(superuser_login):
    # 1. 会社名を登録
    create_resp = superuser_login.post("/companies", json={"name": "LogicTest"})
    assert create_resp.status_code == 201
    company_id_1 = create_resp.json["id"]

    # 2. 会社を論理削除
    delete_resp = superuser_login.delete(f"/companies/{company_id_1}")
    assert delete_resp.status_code == 200

    # 3. 同じ会社名を登録（成功）
    create_resp_2 = superuser_login.post("/companies", json={"name": "LogicTest"})
    assert create_resp_2.status_code == 201
    company_id_2 = create_resp_2.json["id"]

    # 4. 先に論理削除した会社を復活（不成功：同名の現役会社が存在するため）
    restore_resp_fail = superuser_login.post(f"/companies/{company_id_1}/restore")
    data = restore_resp_fail.get_json()
    assert restore_resp_fail.status_code == 400
    message = data['errors']['json'].get("message", "")
    print(message)
    assert any("already exists" in m for m in message)

    # 5. 同じ会社を論理削除（company_id_2を削除）
    delete_resp_2 = superuser_login.delete(f"/companies/{company_id_2}")
    assert delete_resp_2.status_code == 200

    # 6. 先に論理削除した会社を復活（成功）
    restore_resp_success = superuser_login.post(f"/companies/{company_id_1}/restore")
    assert restore_resp_success.status_code == 200

    # 復活後、通常取得できる
    restored_get = superuser_login.get(f"/companies/{company_id_1}")
    assert restored_get.status_code == 200
    assert restored_get.json["name"] == "LogicTest"
