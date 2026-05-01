import pytest
from app import db
from app.models import Company, Organization
from tests.utils import check_response_message

def test_create_organization(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    res = client.post('/organizations', json={
        'name': '営業部',
        'org_code': 'sales',
        'parent_id': root_org['id']
    })
    print(res.get_json())
    assert res.status_code == 201
    data = res.get_json()
    assert data['name'] == '営業部'
    assert data['org_code'] == 'sales'

def test_create_root_organization_twice(login_as_user, superuser):
    client = login_as_user(superuser['email'], superuser["password"])
    company_res = client.post("/companies", json={'name':'test_create_root_organization_twice'})
    assert company_res.status_code == 201
    company_res = company_res.get_json()
    # 最初のルート組織作成
    res1 = client.post('/organizations', json={
        'name': 'root',
        'org_code': 'code',
        'company_id': company_res['id'],
    })
    assert res1.status_code == 201

    # 2つ目はエラー
    res2 = client.post('/organizations', json={
        'name': 'AnotherRoot',
        'org_code': 'root2',
        'company_id': company_res['id']
    })
    assert res2.status_code == 400
    assert check_response_message('ルート組織', res2.get_json())

def test_get_organizations(login_as_user, test_company, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    res = client.get(f'/organizations?company_id={test_company['id']}')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert any(org['name'] == root_org['name'] for org in data)
    # company_idがない場合もエラーにならない
    res = client.get('/organizations')
    assert res.status_code == 200

def test_get_organization_by_id(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    res = client.get(f'/organizations/{root_org['id']}')
    assert res.status_code == 200
    assert res.get_json()['name'] == root_org['name']

def test_update_organization(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    res = client.put(f'/organizations/{root_org['id']}', json={
        'name': '新しい名前',
        'parent_id': None
    })
    assert res.status_code == 200
    assert res.get_json()['name'] == '新しい名前'

def test_delete_organization_with_children(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    parent_id = root_org['id']
    company_id = root_org['company_id']

    # 1. 子組織を作成
    res_create_child = client.post('/organizations', json={
        'name': '子組織',
        'org_code': 'child01',
        'parent_id': parent_id
    })
    assert res_create_child.status_code == 201
    child_org = res_create_child.get_json()
    child_id = child_org['id']

    # 2. ルート組織の削除（失敗するはず）
    res_delete_root = client.delete(f'/organizations/{parent_id}')
    assert res_delete_root.status_code == 400
    assert check_response_message('削除できません', res_delete_root.get_json())

    # 3. 子組織を削除（成功するはず）
    res_delete_child = client.delete(f'/organizations/{child_id}')
    assert res_delete_child.status_code == 200

    # 4. 子組織が削除されたか確認（/children）
    res_check_children = client.get(f'/organizations/{parent_id}/children')
    assert res_check_children.status_code == 200
    children = res_check_children.get_json()
    assert all(c['id'] != child_id for c in children)

def test_get_organization_tree(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    res = client.get(f'/organizations/tree?company_id={root_org['company_id']}')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    #company_idない場合はエラー
    res = client.get(f'/organizations/tree')
    assert res.status_code == 200


def test_get_children(login_as_user, root_org, system_related_users):
    system_admin = system_related_users['system_admin']
    client = login_as_user(system_admin['email'], system_admin['password'])
    child = Organization(
        name="子組織",
        org_code="child",
        parent_id=root_org['id'],
        company_id=root_org['company_id']
    )
    db.session.add(child)
    db.session.commit()

    res = client.get(f'/organizations/{root_org['id']}/children')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert any(org['name'] == '子組織' for org in data)
