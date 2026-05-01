from typing import Any, Dict
import pytest
import json

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


# --- Test Code ---
def test_user_with_scopes_response_structure(system_admin_client):
    """ユーザー一覧APIのレスポンスがUserWithScopesSchemaの形式に準拠しているかテスト"""
    
    # APIエンドポイントを呼び出し
    response = system_admin_client.get('/users')
    
    # ステータスコードの確認
    assert response.status_code == 200
    
    # JSONレスポンスの取得
    data = response.get_json()
    print(data)
    # レスポンスがリストであることを確認
    assert isinstance(data, list), "レスポンスはリスト形式である必要があります"
    
    # データが存在する場合のみ構造確認
    if len(data) > 0:
        user = data[0]  # 最初のユーザーデータで確認
        
        # UserSchemaから継承された必須フィールドの確認
        required_user_fields = [
            'id',
            'name', 
            'organization_id',
            'organization_name'
        ]
        
        for field in required_user_fields:
            assert field in user, f"必須フィールド '{field}' が存在しません"
        
        # UserWithScopesSchemaで追加されたフィールドの確認
        assert 'access_scopes' in user, "scopesフィールドが存在しません"
        
        # scopesフィールドの型確認
        assert isinstance(user['access_scopes'], list), "scopesフィールドはリスト形式である必要があります"
        
        # scopesが存在する場合、AccessScopeSchemaの構造確認
        if len(user['access_scopes']) > 0:
            scope = user['access_scopes'][0]
            
            # AccessScopeの必須フィールド確認
            required_scope_fields = [
                'id',
                'user_id',
                'organization_id', 
                'role'
            ]
            
            for field in required_scope_fields:
                assert field in scope, f"scopeの必須フィールド '{field}' が存在しません"
        
        # 除外されるべきフィールドが含まれていないことを確認
        excluded_fields = ['password_hash']
        for field in excluded_fields:
            assert field not in user, f"除外されるべきフィールド '{field}' が含まれています"


def test_user_with_scopes_empty_response(system_admin_client):
    """ユーザーが存在しない場合のレスポンス構造テスト"""
    
    # 空のレスポンスを想定したテスト
    response = system_admin_client.get('/users')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # 空のリストでも正常な構造であることを確認
    assert isinstance(data, list), "空の場合でもリスト形式である必要があります"


def test_user_with_scopes_field_types(system_admin_client):
    """フィールドの型が正しいかテスト"""
    
    response = system_admin_client.get('/users')
    assert response.status_code == 200
    
    data = response.get_json()
    
    if len(data) > 0:
        user = data[0]
        
        # 各フィールドの型確認
        assert isinstance(user['id'], int), "idは整数である必要があります"
        assert isinstance(user['name'], str), "nameは文字列である必要があります"
        assert isinstance(user['organization_id'], int), "organization_idは整数である必要があります"
        assert isinstance(user['organization_name'], (str, type(None))), "organization_nameは文字列またはNullである必要があります"
        assert isinstance(user['access_scopes'], list), "scopesはリストである必要があります"
        
        # scopesの中身の型確認
        for scope in user['access_scopes']:
            assert isinstance(scope['id'], int), "scope.idは整数である必要があります"
            assert isinstance(scope['user_id'], int), "scope.user_idは整数である必要があります"
            assert isinstance(scope['organization_id'], int), "scope.organization_idは整数である必要があります"
            assert isinstance(scope['role'], str), "scope.roleは文字列である必要があります"


def test_user_with_scopes_role_enum_values(system_admin_client):
    """roleフィールドが適切なenum値かテスト"""
    
    response = system_admin_client.get('/users')
    assert response.status_code == 200
    
    data = response.get_json()
    
    # 有効なロール値を定義
    valid_roles = ['SYSTEM_ADMIN', 'ORG_ADMIN', 'MEMBER']  # OrgRoleEnumの値に合わせて調整
    
    if len(data) > 0:
        for user in data:
            for scope in user['access_scopes']:
                assert scope['role'] in valid_roles, f"無効なrole値: {scope['role']}"