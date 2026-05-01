
import json
import time

from flask.testing import FlaskClient
def test_ai_post_process_task(system_admin_client:FlaskClient):


    from app.celery_app import celery

    print("broker:", celery.conf.broker_url)
    print("backend:", celery.conf.result_backend)
    
    payload = {
        "mode": "task_name",
        "task_info":{
           "title": "Implement user authentication",
           "description": "Create a secure user authentication system using JWT.",
           "deadline": "2023-12-31"
        }
    }
    res = system_admin_client.post("/ai/suggest", json=payload)
    assert res.status_code == 202
    data = res.get_json()
    job_id = data["job_id"]
    assert job_id is not None

    # Polling for job completion
    data = None
    for _ in range(100):
        res = system_admin_client.get(f"/ai/result/{job_id}")
        assert res.status_code == 200
        data = res.get_json()
        state = data['status']
        if state != 'PENDING':
            break
        print(f"Current state: {state}, retrying...")
        time.sleep(1)
    assert data is not None
    print("Final data:", json.dumps(data, indent=2))
    assert data['status'] == 'SUCCESS'
    assert data['mode'] == 'task_name'
    task_data = data.get('task_title_data')
    assert task_data['title'] is not None
    assert task_data['prompt'] is not None
    assert task_data['raw_data'] is not None
    assert data.get('objectives') is None


def test_ai_post_process_objectives(system_admin_client: FlaskClient):
    payload = {
        "mode": "objectives",
        "task_info":{
           "title": "JWTを用いたセキュアなユーザー認証システムを2023年12月31日までに実装する",
           "description": "Create a secure user authentication system using JWT.",
           "deadline": "2023-12-31"
        }
    }
    res = system_admin_client.post("/ai/suggest", json=payload)
    assert res.status_code == 202
    data = res.get_json()
    job_id = data["job_id"]
    assert job_id is not None

    # Polling for job completion
    data = None
    for _ in range(100):
        res = system_admin_client.get(f"/ai/result/{job_id}")
        assert res.status_code == 200
        data = res.get_json()
        state = data['status']
        if state != 'PENDING':
            break
        print("Ai Objective Test Poling",state)
        time.sleep(1)
    assert data is not None
    assert data['status'] == 'SUCCESS'
    assert data['mode'] == 'objectives'
    objectives_data = data.get('objectives_data')
    assert isinstance(objectives_data['objectives'], list)
    objective = objectives_data['objectives'][0]
    assert objective['title'] is not None

    assert objectives_data['prompt'] is not None
    assert objectives_data['raw_data'] is not None
    assert data.get('task_title') is None