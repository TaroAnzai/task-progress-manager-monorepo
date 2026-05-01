import pytest

from app import db
from app.models import Company, Organization, User
from tests.utils import check_response_message

@pytest.fixture
def wp_user_data(root_org):
    return {
        'name': 'ValidUser',
        'email': 'wp_valid@example.com',
        'password': 'password123',
        'role': 'MEMBER',
        'wp_user_id':1234,
        'organization_id':root_org['id']
    }
@pytest.fixture
def wp_user_data2(root_org):
    return{
        'name': 'ValidUser',
        'email': 'valid2@example.com',
        'password': 'password123',
        'role': 'MEMBER',
        'wp_user_id':2222,
        'organization_id':root_org['id']
    }
@pytest.fixture(scope='function')
def created_wp_user_data2(client, wp_user_data2, superuser,login_as_user):
    login_as_user(superuser['email'], superuser["password"])
    res = client.post('/users', json=wp_user_data2)
    assert res.status_code == 201


@pytest.mark.parametrize("role", ["member", "org_admin", "system_admin"])
def test_login_with_email_success(client, system_related_users, role):
    user = system_related_users[role]
    print(user)
    """メールアドレスでのログイン成功テスト"""
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    response = client.post("/sessions", json=login_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "ログイン成功"
    assert data["user"]["name"] == user["name"]

def test_login_with_email_invalid_email(client):
    """存在しないメールアドレスでのログイン失敗テスト"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "anypassword"
    }
    response = client.post("/sessions", json=login_data)
    assert response.status_code == 401
    data = response.get_json()
    assert check_response_message("無効",data)

def test_login_with_email_invalid_password(client, system_related_users):
    user = system_related_users['member']
    """間違ったパスワードでのログイン失敗テスト"""
    login_data = {
        "email": user["email"],
        "password": "wrongpassword"
    }
    response = client.post("/sessions", json=login_data)
    assert response.status_code == 401
    data = response.get_json()
    assert check_response_message("無効", data)


def test_login_with_email_missing_fields(client):
    """必須フィールドが不足している場合のテスト"""
    # emailが不足
    response = client.post("/sessions", json={"password": "testpassword"})
    assert response.status_code == 422
    data = response.get_json()
    assert check_response_message('Missing data for required field.', data, 'email')

    # passwordが不足
    response = client.post("/sessions", json={"email": "test@example.com"})
    assert response.status_code == 422
    data = response.get_json()
    assert check_response_message("Missing data for required field.", data, 'password')

def test_login_with_wp_user_id_success(client, superuser, login_as_user, wp_user_data):
    login_as_user(superuser['email'], superuser["password"])
    res = client.post('/users', json=wp_user_data)
    assert res.status_code == 201

    """wp_user_idでのログイン成功テスト"""
    login_data = {
        "wp_user_id": wp_user_data["wp_user_id"]
    }
    response = client.post("/sessions/by-id", json=login_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "ログイン成功"
    assert data["user"]["wp_user_id"] == wp_user_data["wp_user_id"]
    assert data["user"]["name"] == wp_user_data["name"]

def test_login_with_wp_user_id_not_found(client):
    """存在しないwp_user_idでのログイン失敗テスト"""
    login_data = {
        "wp_user_id": 99999
    }
    response = client.post("/sessions/by-id", json=login_data)
    assert response.status_code == 404
    data = response.get_json()
    assert check_response_message("見つかりません", data)

def test_login_with_wp_user_id_missing_field(client):
    """wp_user_idが不足している場合のテスト"""
    response = client.post("/sessions/by-id", json={})
    assert response.status_code == 422
    data = response.get_json()
    assert check_response_message("Missing data for required field.", data, 'wp_user_id')

@pytest.mark.parametrize("role", ["member", "org_admin", "system_admin"])
def test_get_current_user_authenticated(client, system_related_users, role):
    user = system_related_users[role]
    """認証済みユーザーの現在のユーザー情報取得テスト"""
    # まずログイン
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    login_response = client.post("/sessions", json=login_data)
    assert login_response.status_code == 200

    # 現在のユーザー情報を取得
    response = client.get("/sessions/current")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == user["name"]
    assert data["organization_id"] == user["organization_id"]
    assert "organization_name" in data

def test_get_current_user_unauthenticated(client):
    """未認証状態での現在のユーザー情報取得テスト ログインしていなくても取得は可能だがだが
    からデータが返る"""
    # 念のためログアウトしてセッションを初期化
    client.delete("/sessions/current")
    """未認証状態での現在のユーザー情報取得テスト"""

    response = client.get("/sessions/current")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == ''
    assert data["organization_id"] == None
    assert data["organization_name"] == None

@pytest.mark.parametrize("role", ["member", "org_admin", "system_admin"])
def test_logout_authenticated(client, system_related_users, role):
    user = system_related_users[role]
    """認証済みユーザーのログアウトテスト"""
    # まずログイン
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    login_response = client.post("/sessions", json=login_data)
    assert login_response.status_code == 200

    # ログアウト
    response = client.delete("/sessions/current")
    assert response.status_code == 200
    data = response.get_json()
    assert "ログアウト" in data["message"]

    # ログアウト後は現在のユーザー情報が取得できない
    response = client.get("/sessions/current")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == ''
    assert data["organization_id"] == None
    assert data["organization_name"] == None

def test_logout_unauthenticated(client):
    """未認証状態でのログアウトテスト"""
    response = client.delete("/sessions/current")
    assert response.status_code == 401
    data = response.get_json()
    assert check_response_message("ログインが必要", data)

@pytest.mark.parametrize("role", ["member", "org_admin", "system_admin"])
def test_login_logout_flow(client,  system_related_users, role):
    user = system_related_users[role]
    """ログイン→ユーザー情報取得→ログアウトの一連の流れをテスト"""
    # 1. ログイン
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    login_response = client.post("/sessions", json=login_data)
    assert login_response.status_code == 200

    # 2. 現在のユーザー情報取得
    current_user_response = client.get("/sessions/current")
    assert current_user_response.status_code == 200
    user_data = current_user_response.get_json()
    assert user_data["name"] == user["name"]

    # 3. ログアウト
    logout_response = client.delete("/sessions/current")
    assert logout_response.status_code == 200

    # 4. ログアウト後は認証が必要なエンドポイントにアクセスできない
    current_user_response = client.get("/sessions/current")
    assert current_user_response.status_code == 200
    data = current_user_response.get_json()
    assert data["name"] == ''
    assert data["organization_id"] == None
    assert data["organization_name"] == None

@pytest.mark.parametrize("role", ["member", "org_admin", "system_admin"])
def test_multiple_login_attempts(client,  system_related_users, role):
    user = system_related_users[role]
    """複数回のログイン試行テスト"""
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    
    # 複数回ログインしても成功する
    for i in range(3):
        response = client.post("/sessions", json=login_data)
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "ログイン成功"

def test_login_with_different_methods(client, created_wp_user_data2, wp_user_data2):
    user = wp_user_data2
    """異なるログイン方法でのテスト"""
    # wp_user_idでログイン
    wp_login_data = {
        "wp_user_id": user["wp_user_id"]
    }
    wp_response = client.post("/sessions/by-id", json=wp_login_data)
    assert wp_response.status_code == 200

    # ログアウト
    logout_response = client.delete("/sessions/current")
    assert logout_response.status_code == 200

    # 今度はメールアドレスでログイン
    email_login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    email_response = client.post("/sessions", json=email_login_data)
    assert email_response.status_code == 200