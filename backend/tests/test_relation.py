
import json
from unittest import result

from sqlalchemy import exists, select, text

from app.models import Organization, db, AccessScope, Task, User, ProgressUpdate,TaskAccessUser, TaskAccessOrganization,UserTaskOrder
def test_relation(client,superuser, login_as_user):
    # スーパーユーザーでログイン
    res = client.post("/sessions", json={"email": superuser["email"], "password": superuser["password"]})
    assert res.status_code == 200
    companies_res = client.post("/companies", json={"name": "RerationTestCompany"})
    assert companies_res.status_code == 201
    company = companies_res.get_json()
    #Make Root Organizaion
    res = client.post("/organizations", json={
    "name": "RootOrg",
    "org_code": "root",
    "company_id": company["id"]
    })
    assert res.status_code == 201
    root_org = res.get_json()
    # Make Admin user
    res = client.post("/users",json={
        "name": "admin",
        "email":"admin@test.compa.com",
        "password": "password",
        "role":"SYSTEM_ADMIN",
        "organization_id":root_org["id"]
    })
    assert res.status_code == 201
    admin_user = res.get_json()["user"]
    admin_user["password"] = "password"
    admin_user["email"]="admin@test.compa.com"
    #login by admin_user
    admin_client =  login_as_user(admin_user["email"], admin_user["password"])

    #Make child organizaion
    res = admin_client.post("/organizations", json={
    "name": "ChildOrg",
    "org_code":"child",
    "parent_id": root_org["id"],
    "company_id": company["id"]
    })
    assert res.status_code == 201
    child_org = res.get_json()

    #Make member user
    res = client.post("/users",json={
        "name": "member",
        "email":"member@test.compa.com",
        "password": "password",
        "role":"MEMBER",
        "organization_id":child_org["id"]
    })
    assert res.status_code == 201
    member_user = res.get_json()["user"]
    member_user["password"] = "password"
    member_user["email"]="member@test.compa.com"

    #Make member2 user
    res = client.post("/users",json={
        "name": "member2",
        "email":"member2@test.compa.com",
        "password": "password",
        "role":"MEMBER",
        "organization_id":child_org["id"]
    })
    assert res.status_code == 201
    member2_user = res.get_json()["user"]
    member2_user["password"] = "password"
    member2_user["email"]="member2@test.compa.com"

    #login by memver user
    member_client =  login_as_user(member_user["email"], member_user["password"])

    #Make task
    res = member_client.post("/tasks",json={
        "title": "task title",
    })
    assert res.status_code == 201
    task = res.get_json()["task"]

    #make objective
    res = member_client.post("/objectives",json={
        "task_id": task["id"],
        "title":"objectives title",
        "due_date":"2025-12-31",
        "status":"IN_PROGRESS",
    })
    assert res.status_code == 201
    objective = res.get_json()["objective"]

    #make progress update
    res = member_client.post(f"/updates/{objective["id"]}", json={
        "status": "UNDEFINED",
        "detail": "update string",
        "report_date": "2025-08-24T14:15:22Z"
    })
    assert res.status_code == 201
 
    #make task user order
    res = member_client.post("/task_orders", json={
        "task_ids" : [task["id"]],
        "user_id" : member_user["id"]
    })
    assert res.status_code == 200

    #set menmer2 to task scope and admin user to full scope
    res = member_client.put(f"/tasks/{task["id"]}/access_levels",json ={
        "user_access":[{
            "user_id": member2_user["id"],
            "access_level": "VIEW"
            },
            {
            "user_id": admin_user["id"],
            "access_level": "FULL"
            }
            ],
        "organization_access":[],
    })
    assert res.status_code == 200
    #set member2 to objective assign
    res = member_client.put(f"/objectives/{objective["id"]}",json={
        "assigned_user_id":member2_user["id"]
    })
    assert res.status_code == 200

    res = member_client.get(f"/organizations/{root_org["id"]}")
    assert res.status_code == 200
    org = res.get_json()
    print(json.dumps(org, indent=2))

    #-------------------- Check invalit operation ---------------------------
    #log in by super user
    super_client =  login_as_user(superuser["email"], superuser["password"])
    #failed to delete company
    res = super_client.delete(f"/companies/{company['id']}?force=true")
    assert res.status_code == 400
    #failed to delete organization
    res = super_client.delete(f"/organizations/{root_org["id"]}?force=true")
    assert res.status_code == 400
    res = super_client.delete(f"/organizations/{child_org["id"]}?force=true")
    assert res.status_code == 400
    #log in by admin user
    admin_client =  login_as_user(admin_user["email"], admin_user["password"])
    #failed to delete user
    res = admin_client.delete(f"/users/{member_user["id"]}?force=true")
    assert res.status_code == 400
    res = admin_client.delete(f"/users/{member2_user["id"]}?force=true")
    assert res.status_code == 400
    #faild to delete task
    res = admin_client.delete(f"/tasks/{task["id"]}?force=true")
    assert res.status_code == 400

    #faild to delete objective
    res = admin_client.delete(f"/objectives/{objective['id']}?force=true")
    assert res.status_code == 400
    #success to delete update
    res = admin_client.get(f"/updates/{objective['id']}")
    updates = res.get_json()

    for u in updates:
        res = admin_client.delete(f"/updates/{u["id"]}?force=true")
        assert res.status_code == 200
    #success to delete objective
    res = admin_client.delete(f"/objectives/{objective['id']}?force=true")
    assert res.status_code == 200
    #success to delete task
    res = admin_client.delete(f"/tasks/{task["id"]}?force=true")
    assert res.status_code == 200
    #success to delete user
    res = admin_client.delete(f"/users/{member_user["id"]}?force=true")
    assert res.status_code == 200
    res = admin_client.delete(f"/users/{member2_user["id"]}?force=true")
    assert res.status_code == 200
    #success to delete organization
    res = admin_client.delete(f"/organizations/{child_org["id"]}?force=true")
    assert res.status_code == 200
    #false to delete root org due to admin user
    res = admin_client.delete(f"/organizations/{root_org["id"]}?force=true")
    assert res.status_code == 400
    #log in by super user
    super_client =  login_as_user(superuser["email"], superuser["password"])
    #delete admin user
    res = super_client.delete(f"/users/{admin_user["id"]}?force=true")
    assert res.status_code == 200
    #success to delete root org
    res = super_client.delete(f"/organizations/{root_org["id"]}?force=true")
    assert res.status_code == 200
    #success to delete  company
    res = super_client.delete(f"/companies/{company['id']}?force=true")
    assert res.status_code == 200




    






















