# tests/test_company.py

from flask.testing import FlaskClient


def test_create_company(client: FlaskClient, superuser: dict[str, str]):
    # スーパーユーザーでログイン
    res = client.post("/sessions", json={"email": superuser["email"], "password": superuser["password"]})
    assert res.status_code == 200
    payload = {'name': 'TestCompany_test_company'}
    response = client.post('/companies', json=payload)
    assert response.status_code == 201
    company_data = response.get_json()
    assert company_data['name'] == 'TestCompany_test_company'

    response = client.get('/companies')
    assert response.status_code == 200




