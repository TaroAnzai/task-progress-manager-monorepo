# tests/conftest.py

import os
os.environ["FLASK_ENV"] = "testing"

from typing import Any, Callable
from flask import Flask
from flask.testing import FlaskClient

import pytest
from app import create_app, db as _db
from app.models import AccessScope, Organization, Task, TaskAccessUser, User
from app.constants import TASK_ACCESS_LABELS, OrgRoleEnum
from config import Config as BaseConfig
from werkzeug.security import generate_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sqlite3

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

@pytest.fixture(scope='session')
def app():
    app = create_app(BaseConfig)

    with app.app_context():
        #print(f"[pytest] Using DB: {_db.engine.url}") 
        _db.create_all()
        yield app
        _db.session.remove()
        _db.engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def db_session(app: Flask):
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        Session = scoped_session(
            sessionmaker(bind=connection, autoflush=False)
        )

        old_session = _db.session
        _db.session = Session #type: ignore

        try:
            yield Session
        finally:
            transaction.rollback()
            Session.remove()
            connection.close()
            _db.session = old_session

@pytest.fixture(scope='session')
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture(scope="function")
def superuser(app: Flask):
    user = User()
    user.name = "SuperAdmin"
    user.email = "superadmin@example.com"
    user.is_superuser = True
    user.password_hash = generate_password_hash("superpass")
    _db.session.add(user)
    _db.session.commit()
    return {"id": user.id, "email": user.email, "password": "superpass"}


# 2. テスト用会社の登録（エンドポイント）
@pytest.fixture(scope="function")
def test_company(app: Flask):
    from app.models import Company
    company = Company()
    company.name = "TestCompany"
    _db.session.add(company)
    _db.session.commit()

    return {
        "id": company.id,
        "name": company.name
    }

@pytest.fixture(scope="function")
def test_other_company(app: Flask):
    from app.models import Company
    company = Company()
    company.name = "OtherCompany"
    _db.session.add(company)
    _db.session.commit()

    return {
        "id": company.id,
        "name": company.name
    }

# 3. テスト用ルート組織の登録（エンドポイント）
@pytest.fixture(scope="function")
def root_org(app: Flask, test_company:dict[str,Any]):
    from app.models import Organization
    org = Organization()
    org.name = "RootOrg"
    org.org_code = "root"
    org.company_id = test_company["id"]
    _db.session.add(org)
    _db.session.commit()
    return {
        "id": org.id,
        "name": org.name,
        "org_code": org.org_code,
        "company_id": org.company_id
    }

@pytest.fixture(scope="function")
def other_root_org(app: Flask, test_other_company: dict[str, Any]):
    org = Organization()
    org.name = "OtherRootOrg"
    org.org_code = "otherRoot"
    org.company_id = test_other_company["id"]
    _db.session.add(org)
    _db.session.commit()

    return {
        "id": org.id,
        "name": org.name,
        "org_code": org.org_code,
        "company_id": org.company_id
    }


# 4. テスト用ユーザー（systemadmin）をルート組織に登録（エンドポイント）
@pytest.fixture(scope="function")
def systemadmin_user(app: Flask, root_org: dict[str, Any]):

    system_admin = User()
    system_admin.name = "SystemAdmin"
    system_admin.email = "systemadmin@example.com"
    system_admin.password_hash = generate_password_hash("adminpass")
    system_admin.organization_id = root_org["id"]
    _db.session.add(system_admin)
    _db.session.flush() 
    scope = AccessScope()
    scope.user_id = system_admin.id
    scope.organization_id = root_org["id"]
    scope.role = OrgRoleEnum.SYSTEM_ADMIN
    _db.session.add(scope)
    _db.session.commit()
    payload = {
        "id": system_admin.id,
        "name": system_admin.name,
        "email": system_admin.email,
        "password": "adminpass",
        "organization_id": system_admin.organization_id,
        "role": scope.role
    }
    return {"user": payload}
    

@pytest.fixture(scope="function")
def task_access_users(app: Flask, systemadmin_user: dict[str, Any], root_org: dict[str, Any]):
    task = Task()
    task.title = "Test Task"
    task.created_by = systemadmin_user["user"]["id"]
    task.organization_id = root_org["id"]
    _db.session.add(task)
    _db.session.flush()  # ← ここ重要

    access_levels = ["view", "edit", "full", "owner"]
    created_users = {}

    for level in access_levels:
        user = User()
        user.name = f"TaskUser_{level}"
        user.email = f"taskuser_{level}@example.com"
        user.password_hash = generate_password_hash("testpass")
        user.organization_id = root_org["id"]
        _db.session.add(user)
        _db.session.flush() 
        access = AccessScope()
        access.user_id = user.id
        access.organization_id = root_org["id"]
        access.role = OrgRoleEnum.MEMBER
        _db.session.add(access)
        _db.session.flush() 
        created_users[level] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": "testpass",
            "organization_id": user.organization_id,
            "role": "MEMBER"
        }

        task_access = TaskAccessUser()
        task_access.task_id = task.id
        task_access.user_id = user.id
        task_access.access_level = next(key for key, value in TASK_ACCESS_LABELS.items() if value == level)
        _db.session.add(task_access)
    _db.session.commit()
    return created_users



@pytest.fixture(scope="function")
def system_related_users(app: Flask, root_org: dict[str, Any],superuser: dict[str, Any]):
    """
    システム関連のユーザー（member, org_admin, system_admin）を作成して返す。
    戻り値: {"member": {...}, "org_admin": {...}, "system_admin": {...}}
    ※ {...} は userデータ + "password" を含む
    """
    roles = ["member", "org_admin", "system_admin"]
    created_users = {}

    for role in roles:
        user = User()
        user.name = f"SystemUser_{role}"
        user.email = f"systemuser_{role}@example.com"
        user.password_hash = generate_password_hash("testpass")
        user.organization_id = root_org["id"]
        _db.session.add(user)
        _db.session.flush() 
        scope = AccessScope()
        scope.user_id = user.id
        scope.organization_id = root_org["id"]
        scope.role = getattr(OrgRoleEnum, role.upper())
        _db.session.add(scope)
        _db.session.commit()
        created_users[role] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": "testpass",
            "organization_id": user.organization_id,
            "role": scope.role 
        }
    return created_users


@pytest.fixture(scope="function")
def superuser_login(client: FlaskClient, superuser: dict[str, Any]):
    """スーパーユーザーでログインした状態を返す"""
    res = client.post("/sessions", json={
        "email": superuser["email"],
        "password": superuser["password"]
    })
    assert res.status_code == 200
    yield client
    client.delete("/sessions/current")

@pytest.fixture(scope="function")
def login_as_user(client: FlaskClient):
    """任意ユーザーでログインするためのヘルパー"""
    def _login(email: str, password: str) -> FlaskClient:
        client.delete("/sessions/current")  # 念のためログアウト
        res = client.post("/sessions", json={"email": email, "password": password})
        assert res.status_code == 200
        return client
    yield _login
    client.delete("/sessions/current")

@pytest.fixture(scope="function")
def system_admin_client(systemadmin_user: dict[str, Any], login_as_user: Callable[[str, str], FlaskClient]) -> FlaskClient:
    """システム管理者でログインしたクライアントを返す"""
    client = login_as_user(systemadmin_user["user"]["email"], "adminpass")
    return client

@pytest.fixture(scope="function")
def setup_task_access(system_admin_client: FlaskClient, task_access_users: dict[str, Any]):
    def _setup_task_access(task: dict[str, Any]) -> int:
        """タスクに対して各ユーザーのアクセス権限を設定"""
        task_id = task["id"]

        user_access = [
            {"user_id": task_access_users[level]["id"], "access_level": level.upper()}
            for level in ["view", "edit", "full", "owner"]
        ]
        org_access = []  # 必要に応じて組織アクセスも設定可能

        res = system_admin_client.put(
            f"/tasks/{task_id}/access_levels",
            json={"user_access": user_access, "organization_access": org_access}
        )
        assert res.status_code == 200
        return task_id
    return _setup_task_access