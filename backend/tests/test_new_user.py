def test_full_user_creation_flow(superuser_login, superuser):
    # ① Company を作成
    company_payload = {'name': 'TestCompanyX'}
    company_res = superuser_login.post('/companies', json=company_payload)
    assert company_res.status_code == 201
    company = company_res.json
    assert company['name'] == 'TestCompanyX'

    # ② Organization を作成
    org_payload = {
        'name': 'DevelopmentDept',
        'org_code': 'DEV01',
        'company_id': company['id'],
        'parent_id': None,
        'level': 1
    }
    org_res = superuser_login.post('/organizations', json=org_payload)
    assert org_res.status_code == 201
    org = org_res.json
    assert org['name'] == 'DevelopmentDept'
    assert org['company_id'] == company['id']

    # ③ ユーザーを作成
    user_payload = {
        'name': 'testuser1',
        'email': 'testuser1@example.com',
        'password': 'testpass123',
        'organization_id': org['id'],
    }
    user_res = superuser_login.post('/users', json=user_payload)
    assert user_res.status_code == 201
    user = user_res.json['user']
    assert user['name'] == 'testuser1'
    assert user['organization_id'] == org['id']
