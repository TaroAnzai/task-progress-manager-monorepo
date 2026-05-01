import pytest


@pytest.fixture(scope="function")
def valid_status_id(client):
    res = client.get("/tasks/statuses")
    assert res.status_code == 200
    return res.get_json()[0]["enum"].upper()


@pytest.fixture(scope="function")
def objective_for_progress(system_admin_client, setup_task_access):
    # create task
    task_res = system_admin_client.post("/tasks", json={"title": "Progress Task"})
    assert task_res.status_code == 201
    task = task_res.get_json()["task"]
    # set access rights for view/edit/full/owner users
    setup_task_access(task)
    # create objective under the task
    obj_res = system_admin_client.post(
        "/objectives", json={"task_id": task["id"], "title": "Progress Objective"}
    )
    assert obj_res.status_code == 201
    objective_id = obj_res.get_json()["objective"]["id"]
    return {"task": task, "objective_id": objective_id}


@pytest.fixture(scope="function")
def progress_payload(valid_status_id):
    return {
        "status": valid_status_id,
        "detail": "test progress",
        "report_date": "2024-01-01",
    }


@pytest.fixture(scope="function")
def created_progress(system_admin_client, objective_for_progress, progress_payload):
    obj_id = objective_for_progress["objective_id"]
    res = system_admin_client.post(
        f"/updates/{obj_id}", json=progress_payload
    )
    assert res.status_code == 201
    list_res = system_admin_client.get(
        f"/updates/{obj_id}"
    )
    assert list_res.status_code == 200
    progress_id = list_res.get_json()[-1]["id"]
    return {"id": progress_id, "objective_id": obj_id}


@pytest.mark.parametrize(
    "level, expected",
    [
        ("view", 403),
        ("edit", 201),
        ("full", 201),
        ("owner", 201),
    ],
)
def test_add_progress_permission(
    login_as_user, task_access_users, objective_for_progress, progress_payload, level, expected
):
    user = task_access_users[level]
    client = login_as_user(user["email"], user["password"])
    print(progress_payload)
    res = client.post(
        f"/updates/{objective_for_progress['objective_id']}",
        json=progress_payload,
    )
    assert res.status_code == expected


def test_get_progress_list_view(login_as_user, task_access_users, created_progress):
    user = task_access_users["view"]
    client = login_as_user(user["email"], user["password"])
    res = client.get(
        f"/updates/{created_progress['objective_id']}"
    )
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_get_latest_progress(login_as_user, task_access_users, objective_for_progress, valid_status_id):
    obj_id = objective_for_progress["objective_id"]
    user = task_access_users["full"]
    client = login_as_user(user["email"], user["password"])
    client.post(
        f"/updates/{obj_id}",
        json={"status": valid_status_id, "detail": "old", "report_date": "2024-01-01"},
    )
    client.post(
        f"/updates/{obj_id}",
        json={"status": valid_status_id, "detail": "new", "report_date": "2024-02-01"},
    )
    res = client.get(f"/updates/{obj_id}/latest-progress")
    assert res.status_code == 200
    assert res.get_json()["detail"] == "new"


@pytest.mark.parametrize(
    "level, expected",
    [
        ("view", 403),
        ("edit", 200),
        ("full", 200),
        ("owner", 200),
    ],
)
def test_delete_progress_permission(
    login_as_user, task_access_users, created_progress, level, expected
):
    user = task_access_users[level]
    client = login_as_user(user["email"], user["password"])
    res = client.delete(
        f"/updates/{created_progress['id']}"
    )
    assert res.status_code == expected


def test_delete_progress_not_found(system_admin_client):
    res = system_admin_client.delete(
        "/updates/99999"
    )
    assert res.status_code == 404
