from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient
import pytest
from werkzeug.security import generate_password_hash

from app.models import (
    AccessSubject,
    AccessSubjectType,
    Group,
    GroupScopeType,
    Organization,
    Task,
    TaskAccess,
    User,
)
from app.constants import TaskAccessLevelEnum
from app import db
@pytest.fixture(scope="function")
def task_for_access_subject_search(
    systemadmin_user: dict[str, Any],
    root_org: dict[str, Any],
) -> dict[str, Any]:
    """
    アクセス対象検索用のタスクを作成する。
    """
    task = Task()
    task.title = "Access Subject Search Test Task"
    task.description = "アクセス対象検索テスト用タスク"
    task.created_by = systemadmin_user["user"]["id"]
    task.organization_id = root_org["id"]

    db.session.add(task)
    db.session.flush()

    return {
        "id": task.id,
        "title": task.title,
        "created_by": task.created_by,
        "organization_id": task.organization_id,
    }


@pytest.fixture(scope="function")
def access_subject_search_data(
    systemadmin_user: dict[str, Any],
    root_org: dict[str, Any],
    task_for_access_subject_search: dict[str, Any],
) -> dict[str, Any]:
    """
    検索対象となるユーザー・組織・グループを作成する。

    - USER: 営業 太郎
    - ORGANIZATION: 営業部
    - GROUP: 営業管理グループ
    - 追加済み確認用に、営業部を TaskAccess に登録する
    """

    # -------------------------
    # Organization
    # -------------------------
    sales_org = Organization()
    sales_org.name = "営業部"
    sales_org.org_code = "sales"
    sales_org.company_id = root_org["company_id"]
    sales_org.parent_id = root_org["id"]
    sales_org.level = 2
    db.session.add(sales_org)
    db.session.flush()

    # -------------------------
    # User
    # -------------------------
    sales_user = User()
    sales_user.name = "営業 太郎"
    sales_user.email = "sales.taro@example.com"
    sales_user.password_hash = generate_password_hash("testpass")
    sales_user.organization_id = sales_org.id
    db.session.add(sales_user)
    db.session.flush()

    # 検索に引っかからない確認用ユーザー
    other_user = User()
    other_user.name = "開発 花子"
    other_user.email = "dev.hanako@example.com"
    other_user.password_hash = generate_password_hash("testpass")
    other_user.organization_id = root_org["id"]
    db.session.add(other_user)
    db.session.flush()

    # -------------------------
    # Group
    # -------------------------
    sales_group = Group()
    sales_group.name = "営業管理グループ"
    sales_group.owner_user_id = systemadmin_user["user"]["id"]
    sales_group.organization_id = sales_org.id
    sales_group.scope_type = GroupScopeType.ORGANIZATION
    db.session.add(sales_group)
    db.session.flush()

    # -------------------------
    # already_added確認用
    # 営業部をタスクにVIEWで登録しておく
    # -------------------------
    org_subject = AccessSubject()
    org_subject.subject_type = AccessSubjectType.ORGANIZATION
    org_subject.ref_id = sales_org.id
    db.session.add(org_subject)
    db.session.flush()

    task_access = TaskAccess()
    task_access.task_id = task_for_access_subject_search["id"]
    task_access.subject_id = org_subject.id
    task_access.access_level = TaskAccessLevelEnum.VIEW
    db.session.add(task_access)
    db.session.flush()

    return {
        "task_id": task_for_access_subject_search["id"],
        "sales_org": {
            "id": sales_org.id,
            "name": sales_org.name,
            "org_code": sales_org.org_code,
        },
        "sales_user": {
            "id": sales_user.id,
            "name": sales_user.name,
            "email": sales_user.email,
        },
        "sales_group": {
            "id": sales_group.id,
            "name": sales_group.name,
        },
        "other_user": {
            "id": other_user.id,
            "name": other_user.name,
        },
    }


def _find_subject(
    subjects: list[dict[str, Any]],
    *,
    subject_type: str,
    ref_id: int,
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in subjects
            if item["subject_type"] == subject_type and item["ref_id"] == ref_id
        ),
        None,
    )


class TestTaskAccessSubjectSearch:
    def test_search_access_subjects_returns_users_organizations_and_groups(
        self,
        system_admin_client:FlaskClient,
        access_subject_search_data: dict[str, Any],
    ):
        """
        keyword=営業 で USER / ORGANIZATION / GROUP が横断検索できること。
        """
        res = system_admin_client.get(
            f"/tasks/access_subjects/search",
            query_string={
                "keyword": "営業",
                "limit": 20,
            },
        )

        assert res.status_code == 200

        data = res.get_json()
        assert isinstance(data, dict)
        assert "subjects" in data
        assert isinstance(data["subjects"], list)

        subjects = data["subjects"]

        sales_user = _find_subject(
            subjects,
            subject_type="USER",
            ref_id=access_subject_search_data["sales_user"]["id"],
        )
        sales_org = _find_subject(
            subjects,
            subject_type="ORGANIZATION",
            ref_id=access_subject_search_data["sales_org"]["id"],
        )
        sales_group = _find_subject(
            subjects,
            subject_type="GROUP",
            ref_id=access_subject_search_data["sales_group"]["id"],
        )

        assert sales_user is not None
        assert sales_user["display_name"] == "営業 太郎"
        assert sales_user["description"] == "sales.taro@example.com"

        assert sales_org is not None
        assert sales_org["display_name"] == "営業部"

        assert sales_group is not None
        assert sales_group["display_name"] == "営業管理グループ"

        # 検索語に一致しないユーザーは含まれない
        other_user = _find_subject(
            subjects,
            subject_type="USER",
            ref_id=access_subject_search_data["other_user"]["id"],
        )
        assert other_user is None

    def test_search_access_subjects_can_filter_by_subject_type_user(
        self,
        system_admin_client:FlaskClient,
        access_subject_search_data: dict[str, Any],
    ):
        """
        subject_type=USER を指定した場合、USER のみ返ること。
        """
        res = system_admin_client.get(
            f"/tasks/access_subjects/search",
            query_string={
                "keyword": "営業",
                "subject_type": "USER",
                "limit": 20,
            },
        )

        assert res.status_code == 200

        data = res.get_json()
        subjects = data["subjects"]

        assert len(subjects) >= 1
        assert all(item["subject_type"] == "USER" for item in subjects)

        sales_user = _find_subject(
            subjects,
            subject_type="USER",
            ref_id=access_subject_search_data["sales_user"]["id"],
        )
        assert sales_user is not None
        assert sales_user["display_name"] == "営業 太郎"

    def test_search_access_subjects_can_filter_by_subject_type_organization(
        self,
        system_admin_client:FlaskClient,
        access_subject_search_data: dict[str, Any],
    ):
        """
        subject_type=ORGANIZATION を指定した場合、ORGANIZATION のみ返ること。
        """
        res = system_admin_client.get(
            f"/tasks/access_subjects/search",
            query_string={
                "keyword": "営業",
                "subject_type": "ORGANIZATION",
                "limit": 20,
            },
        )

        assert res.status_code == 200

        data = res.get_json()
        subjects = data["subjects"]

        assert len(subjects) >= 1
        assert all(item["subject_type"] == "ORGANIZATION" for item in subjects)

        sales_org = _find_subject(
            subjects,
            subject_type="ORGANIZATION",
            ref_id=access_subject_search_data["sales_org"]["id"],
        )
        assert sales_org is not None
        assert sales_org["display_name"] == "営業部"

    def test_search_access_subjects_can_filter_by_subject_type_group(
        self,
        system_admin_client:FlaskClient,
        access_subject_search_data: dict[str, Any],
    ):
        """
        subject_type=GROUP を指定した場合、GROUP のみ返ること。
        """
        res = system_admin_client.get(
            f"/tasks/access_subjects/search",
            query_string={
                "keyword": "営業",
                "subject_type": "GROUP",
                "limit": 20,
            },
        )

        assert res.status_code == 200

        data = res.get_json()
        subjects = data["subjects"]

        assert len(subjects) >= 1
        assert all(item["subject_type"] == "GROUP" for item in subjects)

        sales_group = _find_subject(
            subjects,
            subject_type="GROUP",
            ref_id=access_subject_search_data["sales_group"]["id"],
        )
        assert sales_group is not None
        assert sales_group["display_name"] == "営業管理グループ"


    def test_search_access_subjects_requires_keyword(
        self,
        system_admin_client:FlaskClient,
        access_subject_search_data: dict[str, Any],
    ):
        """
        keyword未指定の場合はバリデーションエラーになること。
        """
        res = system_admin_client.get(
            f"/tasks/access_subjects/search",
            query_string={
                "limit": 20,
            },
        )

        assert res.status_code == 422
