from typing import Any, Dict

import pytest

from tests.utils import check_response_message

# --- Constants ---
VALID_USER_DATA = {
    'name': 'ValidUser',
    'email': 'valid@example.com',
    'password': 'password123',
    'role': 'MEMBER'
}


# --- Helper Functions ---
def create_user_payload(org_id: int, **overrides) -> Dict[str, Any]:
    """ユーザー作成用のペイロードを生成"""
    payload = {**VALID_USER_DATA, 'organization_id': org_id}
    payload.update(overrides)
    return payload

def assert_user_created(response, expected_name: str = None):
    """ユーザー作成レスポンスの共通アサーション"""
    assert response.status_code == 201
    user = response.get_json()['user']
    if expected_name:
        assert user['name'] == expected_name
    return user

# --- Test Classes ---
class TestUserCreation:
    """ユーザー作成に関するテスト"""
    def test_create_user_valid(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """有効なデータでユーザー作成"""
        payload = create_user_payload(root_org['id'])
        res = client.post('/users', json=payload)
        assert_user_created(res, 'ValidUser')
    
    def test_create_user_missing_fields(self, login_as_user, system_related_users):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """必須フィールド不足でユーザー作成失敗"""
        res = client.post('/users', json={'email': 'incomplete@example.com'})
        assert res.status_code == 422
        data = res.get_json()
        for field in ['name', 'password', 'organization_id']:
            assert check_response_message('Missing data for required field.', data, field)
    
    def test_create_user_duplicate_email(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """重複メールアドレスでユーザー作成失敗"""
        # まず最初のユーザーを作成
        first_payload = create_user_payload(
            root_org['id'],
            name='FirstUser',
            email='duplicate@example.com'
        )
        first_res = client.post('/users', json=first_payload)
        assert_user_created(first_res)
        
        # 同じメールアドレスで2回目の登録を試行
        second_payload = create_user_payload(
            root_org['id'],
            name='SecondUser',
            email='duplicate@example.com'  # 重複メール
        )
        res = client.post('/users', json=second_payload)
        assert res.status_code == 400
        assert check_response_message('このメールアドレスは既に使用されています。', res.get_json())

class TestUserRetrieval:
    """ユーザー取得に関するテスト"""
    
    def test_get_user_not_found(self, login_as_user, system_related_users):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """存在しないユーザーの取得"""
        res = client.get('/users/999999')
        assert res.status_code == 404
    
    def test_get_user_by_email(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """メールアドレスでユーザー取得"""
        # テスト用ユーザーを作成
        email = 'email_lookup@example.com'
        payload = create_user_payload(root_org['id'], email=email)
        client.post('/users', json=payload)
        
        # メールアドレスでユーザー取得
        res = client.get(f'/users/email/{email}')
        assert res.status_code == 200
        responce_data = res.get_json()
        assert responce_data['name'] == payload['name']
    
    def test_get_user_by_wp_user_id(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """WordPress User IDでユーザー取得"""
        wp_user_id = 1001
        payload = create_user_payload(
            root_org['id'],
            name='WPID',
            email='wpid@example.com',
            wp_user_id=wp_user_id
        )
        client.post('/users', json=payload)
        
        res = client.get(f'/users/wp/{wp_user_id}')
        assert res.status_code == 200
        responce_data= res.get_json()
        assert responce_data['wp_user_id'] == wp_user_id
    
    def test_get_users_by_org_tree(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """組織ツリーでユーザー一覧取得"""
        res = client.get(f'/users/by-org-tree/{root_org["id"]}')
        assert res.status_code == 200
        users = res.get_json()
        assert isinstance(users, list)

class TestUserModification:
    """ユーザー更新・削除に関するテスト"""
    
    def test_update_user(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """ユーザー情報更新"""
        # テストユーザー作成
        payload = create_user_payload(
            root_org['id'],
            name='ToUpdate',
            email='update_me@example.com'
        )
        create_res = client.post('/users', json=payload)
        user_id = assert_user_created(create_res)['id']
        
        # 更新実行
        update_data = {'name': 'UpdatedName'}
        res = client.put(f'/users/{user_id}', json=update_data)
        assert res.status_code == 200
        updated_user = res.get_json()
        assert updated_user['name'] == 'UpdatedName'
    
    def test_delete_user(self, login_as_user, system_related_users, root_org):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """ユーザー削除"""
        # テストユーザー作成
        payload = create_user_payload(
            root_org['id'],
            name='ToDelete',
            email='delete_me@example.com'
        )
        create_res = client.post('/users', json=payload)
        user_id = assert_user_created(create_res)['id']
        
        # 削除実行
        res = client.delete(f'/users/{user_id}')
        assert res.status_code == 200
        message = res.get_json()['message']
        assert '削除' in message

# --- パラメータ化テストの例 ---
class TestUserCreationParameterized:
    """パラメータ化されたユーザー作成テスト"""
    
    @pytest.mark.parametrize("missing_field", [
        'name', 'email', 'password', 'organization_id'
    ])
    def test_create_user_missing_required_fields(self, login_as_user, system_related_users, root_org, missing_field):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """各必須フィールドが不足している場合のテスト"""
        payload = create_user_payload(root_org['id'])
        del payload[missing_field]
        
        res = client.post('/users', json=payload)
        assert res.status_code == 422
        data = res.get_json()
        assert check_response_message('Missing data for required field.', data, missing_field)
    
    @pytest.mark.parametrize("invalid_email", [
        'invalid-email',
        'missing@domain',
        '@missing-local.com',
        'spaces in@email.com'
    ])
    def test_create_user_invalid_email_format(self, login_as_user, system_related_users, root_org, invalid_email):
        system_admin = system_related_users['system_admin']
        client = login_as_user(system_admin['email'], system_admin['password'])
        """無効なメールアドレス形式のテスト"""
        payload = create_user_payload(root_org['id'], email=invalid_email)
        res = client.post('/users', json=payload)
        assert res.status_code == 400
        assert check_response_message('無効なメールアドレス形式です', res.get_json())
    


EXPECTED_USER_KEYS = {
    "id",
    "wp_user_id",
    "name",
    "is_superuser",
    "organization_id",
    "organization_name",
    "company_id",
    "access_scopes"
}

def test_user_fields_in_response(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])

    # ユーザー作成
    email = 'data_item_lookup@example.com'
    payload = create_user_payload(root_org['id'], email=email)
    res = client.post('/users', json=payload)
    assert res.status_code == 201

    # ユーザー取得
    res = client.get(f'/users/email/{email}')
    assert res.status_code == 200

    user_data = res.json
    assert isinstance(user_data, dict), "Response is not a dictionary"

    missing_keys = EXPECTED_USER_KEYS - user_data.keys()
    extra_keys = user_data.keys() - EXPECTED_USER_KEYS

    assert not missing_keys, f"Missing keys in user data: {missing_keys}"
    assert not extra_keys, f"Unexpected extra keys in user data: {extra_keys}"

def test_create_user_duplicate_email_other_company(superuser_login, root_org,other_root_org):
    client = superuser_login
    """別の会社で重複メールアドレスでユーザー作成成功"""
    # まず最初のユーザーを作成
    first_payload = create_user_payload(
        root_org['id'],
        name='FirstUser',
        email='OtherCompany@example.com'
    )
    first_res = client.post('/users', json=first_payload)
    assert_user_created(first_res)
    
    # 同じメールアドレスで2回目の登録を試行
    second_payload = create_user_payload(
        root_org['id'],
        name='SecondUser',
        email='OtherCompany@example.com'  # 重複メール
    )
    res = client.post('/users', json=second_payload)
    assert res.status_code == 400
    assert check_response_message('このメールアドレスは既に使用されています。', res.get_json())

    # 同じメールアドレスで別の会社で登録を試行
    second_payload = create_user_payload(
        other_root_org['id'],
        name='SecondUser',
        email='OtherCompany@example.com'  # 重複メール
    )
    res = client.post('/users', json=second_payload)
    assert res.status_code == 400
    assert check_response_message('このメールアドレスは既に使用されています。', res.get_json())

def test_get_user_deferent_org( login_as_user, system_related_users, root_org):
    #Login as system_admin
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    
    #Make organizarion under root organizarion
    res = client.post('/organizations', json={
        'name': 'Child Organizarion',
        'org_code': 'child11',
        'parent_id': root_org['id']
    })
    print(res.get_json())
    assert res.status_code == 201
    child_org = res.get_json()

    #Make User at root Org
    payload = create_user_payload(
        root_org['id'],
        name = "Test1",
        email='sample1@example.com'  # 他のテストと重複しないメール
    )
    res = client.post('/users', json=payload)
    assert res.status_code == 201

    #MAke User at Child Org
    payload = create_user_payload(
        child_org['id'],
        name = 'Test2',
        email='sample2@example.com'  # 他のテストと重複しないメール
    )
    res = client.post('/users', json=payload)
    assert res.status_code == 201    

    #login as member user
    system_admin = system_related_users['member']
    client = login_as_user(system_admin['email'], system_admin['password'])

    #Can not get user by admin endpoint
    res = client.get(f'/users/admin')
    assert res.status_code == 403

    #get user by nomal by endpoint
    res = client.get(f'/users')
    assert res.status_code == 200
    data = res.get_json()


    # 1. name が Test1 のユーザーデータがあるか
    assert any(user["name"] == "Test1" for user in data), "Test1 のユーザーが見つかりません"

    # 2. name が Test2 のユーザーデータがあるか
    assert any(user["name"] == "Test2" for user in data), "Test2 のユーザーが見つかりません"

    # 3. organization_id が root_org['id'] のデータがあるか
    assert any(user["organization_id"] == root_org["id"] for user in data), \
        f"organization_id={root_org['id']} のユーザーが見つかりません"

    # 4. organization_id が child_org['id'] のデータがあるか
    assert any(user["organization_id"] == child_org["id"] for user in data), \
        f"organization_id={child_org['id']} のユーザーが見つかりません"

    # 5. sample1@example.com のユーザーデータに email キーが無いこと
    sample_user = next((u for u in data if u.get("name") == "Test1") ,None)
    assert "email" not in sample_user, "emailキーが存在してはいけません"

    # 6. その他のキーがすべて存在すること（添付データから）
    expected_keys = {
        "access_scopes",
        "company_id",
        "id",
        "is_superuser",
        "name",
        "organization_id",
        "organization_name",
        "wp_user_id"
    }
    assert expected_keys.issubset(sample_user.keys()), \
        f"必要なキーが不足しています。現在のキー: {sample_user.keys()}"

def test_get_user_for_admin( login_as_user, system_related_users, root_org):
        #Login as system_admin
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    #Make User at root Org
    payload = create_user_payload(
        root_org['id'],
        name = "AdminTest1",
        email='Adminsample1@example.com'  # 他のテストと重複しないメール
    )
    res = client.post('/users', json=payload)
    assert res.status_code == 201

    #get user by admin endpoint
    res = client.get(f'/users/admin')
    assert res.status_code == 200

    #Check all keys in data

    data = res.get_json()

    assert any(user["name"] == "AdminTest1" for user in data), "AdminTest1 のユーザーが見つかりません"
    sample_user = next((u for u in data if u.get("name") == "AdminTest1") ,None)
    expected_keys = {
        "access_scopes",
        "company_id",
        "id",
        "is_superuser",
        "name",
        "organization_id",
        "organization_name",
        "wp_user_id",
        "email"
    }
    assert expected_keys.issubset(sample_user.keys()), \
        f"必要なキーが不足しています。現在のキー: {sample_user.keys()}"