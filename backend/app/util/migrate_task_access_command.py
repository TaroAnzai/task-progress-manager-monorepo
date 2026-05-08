import click
from flask.cli import with_appcontext
from sqlalchemy import select

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
    created_user_accesses, created_user_subjects = register_task_access(list(old_rows), existing_subjects)
    #TaskAccessOrganization
    old_row = session.scalars(
        select(TaskAccessOrganization)
    ).all()
    created_org_accesses, created_org_subjects = register_task_access(list(old_row), existing_subjects)

    if dry_run:
        session.rollback()
    else:
        session.commit()

    click.echo(
        f"created_user_subjects={created_user_subjects}, "
        f"created_user_accesses={created_user_accesses},"
        f"created_org_subjects={created_org_subjects}, "
        f"created_org_accesses={created_org_accesses}"

    )
def register_task_access(
        old_rows:list[TaskAccessUser|TaskAccessOrganization],
        existing_subjects:dict[tuple[AccessSubjectType, int], AccessSubject]
        ) -> tuple[int,int]:
    session = db.session
    created_subjects = 0
    created_accesses = 0
    for row in old_rows:

        if isinstance(row,TaskAccessUser):
            key = (AccessSubjectType.USER, row.user_id)
            subject_id = row.user_id
        else:
            key = (AccessSubjectType.ORGANIZATION, row.organization_id)
            subject_id = row.organization_id

        subject = existing_subjects.get(key)

        if subject is None:
            subject = AccessSubject()
            subject.subject_type=AccessSubjectType.USER
            subject.ref_id=subject_id
            

            session.add(subject)
            session.flush()

            existing_subjects[key] = subject
            created_subjects += 1

        task_access = TaskAccess()
        task_access.task_id=row.task_id
        task_access.subject_id=subject.id
        task_access.access_level=row.access_level

        session.add(task_access)
        created_accesses += 1
    return created_accesses, created_subjects