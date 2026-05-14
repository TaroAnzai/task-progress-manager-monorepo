import click
from flask.cli import with_appcontext
from sqlalchemy import select

from app.constants import TaskAccessLevelEnum
from app.extensions import db
from app.models import (
    TaskAccessOrganization,
    TaskAccessUser,
    TaskAccess,
    AccessSubject,
    AccessSubjectType,
)


@click.command("migrate-task-access")
@click.option("--dry-run", is_flag=True)
@with_appcontext
def migrate_task_access_command(dry_run:bool):
    """
    task_access_user → task_access へ移行
    """

    session = db.session

    existing_subjects = {
        (s.subject_type, s.ref_id): s
        for s in session.scalars(
            select(AccessSubject)
        ).all()
    }

    #TaskAccessUser
    old_rows = session.scalars(
        select(TaskAccessUser)
    ).all()
    created_user_accesses, created_user_subjects,updated_user_accesses = register_task_access(list(old_rows), existing_subjects)
    #TaskAccessOrganization
    old_row = session.scalars(
        select(TaskAccessOrganization)
    ).all()
    created_org_accesses, created_org_subjects, updated_org_accesses = register_task_access(list(old_row), existing_subjects)

    if dry_run:
        session.rollback()
    else:
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    click.echo(
        f"created_user_subjects={created_user_subjects}, "
        f"created_user_accesses={created_user_accesses},"
        f"updated_user_accesses={updated_user_accesses}, "
        f"created_org_subjects={created_org_subjects}, "
        f"created_org_accesses={created_org_accesses}"
        f"updated_org_accesses={updated_org_accesses}"

    )
from sqlalchemy import select

def register_task_access(
    old_rows: list[TaskAccessUser | TaskAccessOrganization],
    existing_subjects: dict[tuple[AccessSubjectType, int], AccessSubject],
) -> tuple[int, int, int]:
    """
    Returns:
        tuple:
            created_accesses: 新規作成した TaskAccess 数
            created_subjects: 新規作成した AccessSubject 数
            updated_accesses: 既存 TaskAccess の権限を更新した数
    """

    session = db.session
    created_subjects = 0
    created_accesses = 0
    updated_accesses = 0

    aggregated: dict[
        tuple[int, AccessSubjectType, int],
        TaskAccessLevelEnum,
    ] = {}

    for row in old_rows:
        if isinstance(row, TaskAccessUser):
            subject_type = AccessSubjectType.USER
            ref_id = row.user_id
        else:
            subject_type = AccessSubjectType.ORGANIZATION
            ref_id = row.organization_id

        key = (row.task_id, subject_type, ref_id)

        current_level = aggregated.get(key)
        if current_level is None or row.access_level > current_level:
            aggregated[key] = row.access_level

    for (task_id, subject_type, ref_id), access_level in aggregated.items():
        subject_key = (subject_type, ref_id)
        subject = existing_subjects.get(subject_key)

        if subject is None:
            subject = AccessSubject()
            subject.subject_type=subject_type
            subject.ref_id=ref_id

            session.add(subject)
            session.flush()

            existing_subjects[subject_key] = subject
            created_subjects += 1

        existing_task_access = session.scalar(
            select(TaskAccess).where(
                TaskAccess.task_id == task_id,
                TaskAccess.subject_id == subject.id,
            )
        )

        if existing_task_access is None:
            task_access = TaskAccess()
            task_access.task_id=task_id
            task_access.subject_id=subject.id
            task_access.access_level=access_level

            session.add(task_access)
            created_accesses += 1
            continue

        if access_level > existing_task_access.access_level:
            existing_task_access.access_level = access_level
            updated_accesses += 1

    return created_accesses, created_subjects, updated_accesses
