from typing import Any

from flask.testing import FlaskClient
import pytest

@pytest.fixture
def group_payload(root_org:dict[str, int|str], system_related_users: dict[str, dict[str, int|str]]):
    return {
            "name": "TestGroup",
            "scope_type": "ORGANIZATION",
            "organization_id": root_org["id"],
            "member_user_ids": [user["id"] for user in system_related_users.values()]
        }

def test_list_group_member(system_admin_client:FlaskClient, group_payload:dict[str, Any]):
    res = system_admin_client.post("/groups", json=group_payload)
    assert res.status_code == 201, res.get_data(as_text=True)
    data = res.get_json()

    res = system_admin_client.get(f"/groups/{data["id"]}/members")
    assert res.status_code == 200, res.get_data(as_text=True)
    data = res.get_json()
    assert data["user_ids"] == group_payload["member_user_ids"], data

def test_update_group_member(system_admin_client:FlaskClient, group_payload:dict[str, Any], root_org:dict[str, int|str]):
    res = system_admin_client.post("/groups", json=group_payload)
    assert res.status_code == 201, res.get_data(as_text=True)
    data = res.get_json()
    user_ids:list[int] = group_payload['member_user_ids']
    group_id:int =  data['id']
    #create new user
    payload =  {
        'name': 'ValidUser',
        'email': 'valid@example.com',
        'password': 'password123',
        'role': 'MEMBER',
        'organization_id': root_org['id']
    }
    res = system_admin_client.post('/users', json=payload)
    assert res.status_code == 201, res.get_data(as_text=True)
    data = res.get_json()['user']

    user_ids.pop(2)
    user_ids.append(data['id'])
    payload ={
        'user_ids':user_ids
    }
    res = system_admin_client.put(f'/groups/{group_id}/members', json=payload)
    assert res.status_code == 200, res.get_data(as_text=True)
    data = res.get_json()
    assert data['user_ids'] == user_ids




