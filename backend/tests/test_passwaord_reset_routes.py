
from tarfile import data_filter
from typing import Any, Dict
import pytest
import re
import app.services.auth_password_reset_service as svc
# --- Constants ---
VALID_USER_DATA = {
    'name': 'Test reset',
    'email': 'sample@example.com',
    'password': 'password123',
    'role': 'MEMBER'
}

# --- Helper Functions ---
def create_user_payload(org_id: int, **overrides) -> Dict[str, Any]:
    """ユーザー作成用のペイロードを生成"""
    payload = {**VALID_USER_DATA, 'organization_id': org_id}
    payload.update(overrides)
    return payload

@pytest.fixture
def reset_sample_user(system_related_users, login_as_user, root_org):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    """テスト用サンプルユーザー"""
    payload = create_user_payload(
        root_org['id']
    )
    res = client.post('/users', json=payload)
    assert res.status_code == 201
    user = res.get_json()['user']
    user['email'] = VALID_USER_DATA['email']
    return user


def test_password_reset_request(client, reset_sample_user):
    # ログアウト
    response = client.delete("/sessions/current")
    payload ={"email" : reset_sample_user['email']}
    res = client.post("/auth/password-reset/request", json = payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "message" in data



def test_password_reset_invalid(client, reset_sample_user, monkeypatch):
    # ログアウト
    response = client.delete("/sessions/current")
    payload ={"email" : "invalid@example.com"}
    res = client.post("/auth/password-reset/request", json = payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "msg" not in data
    assert data['message'] == "Send mail"


def test_password_reset_comfirm(client,reset_sample_user, monkeypatch):
    # ログアウト
    response = client.delete("/sessions/current")
    captured = {}
    def fake_send_email(msg, config):
        captured["msg"] = msg
        return True
    monkeypatch.setattr(svc, "send_email", fake_send_email, raising=False)

    # paswart reset request
    payload ={"email" : reset_sample_user['email']}
    res = client.post("/auth/password-reset/request", json = payload)
    assert res.status_code == 200
    assert "msg" in captured
    TOKEN_RE = re.compile(r"token=([A-Za-z0-9._-]+)")
    m = TOKEN_RE.search(captured['msg'].text)
    assert m is not None
    token = m.group(1)

    #chenge password
    payload = {
        "token":token,
        "new_password":"testttttss"
    }
    res = client.post("/auth/password-reset/confirm",json = payload)
    print("res confirm", res.get_json())
    assert res.status_code == 200


def test_pw_reset_comfirm_invalid_token(client,reset_sample_user, monkeypatch):
    payload = {
        "token":"iiii",
        "new_password":"testttttss"
    }
    res = client.post("/auth/password-reset/confirm",json = payload)
    print(res.get_json())
    assert res.status_code == 400



