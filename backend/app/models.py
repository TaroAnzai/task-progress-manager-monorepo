from enum import IntEnum, auto
from typing import Any, Optional, Protocol, Type, TypeVar

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    ColumnElement,
    Dialect,
    event,
    Boolean,
    UniqueConstraint,
    select,
    ForeignKey,
    String,
    Date,
    DateTime,
    Text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)
from datetime import date, datetime, time, UTC
import sqlite3
from app.extensions import db
from .constants import OrgRoleEnum, TaskAccessLevelEnum, StatusEnum
from .reminder_constants import ReminderConditionEnum, ReminderFrequencyEnum

E = TypeVar("E", bound=IntEnum)
class IntEnumType(db.TypeDecorator):
    impl = db.Integer
    cache_ok = True

    def __init__(self, enumtype:Type[E], *args:object, **kwargs:object) -> None:
        self._enumtype = enumtype
        super().__init__(*args, **kwargs)
        
    def process_bind_param(self, value:IntEnum, dialect:Dialect) -> int|None:
        return value.value if isinstance(value, self._enumtype) else value

    def process_result_value(self, value:int|None, dialect:Dialect) -> IntEnum|None:
        return self._enumtype(value) if value is not None else None

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection:Any, connection_record:Any) -> None:
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# =====================
# BaseModel
# =====================

class BaseModel(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)

# =====================
# SoftDelete
# =====================
class SoftDeletable(Protocol):
    id: int
    is_deleted: bool
    def unique_keys(self) -> list[ColumnElement[bool]]:...

class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    def soft_delete(self):
        self.is_deleted = True

    def restore(self:SoftDeletable) -> None:
        cls = type(self)
        for cond in self.unique_keys():
            exists = db.session.query(cls).filter(
                cls.id != self.id,  #type: ignore[attr-defined]
                cond,
                cls.is_deleted == False  #type: ignore[attr-defined]
            ).first()
            if exists:
                raise ValueError(f"Duplicate on restore: {cond}")

        self.is_deleted = False

    def unique_keys(self) -> list[ColumnElement[bool]]:
        return []

# =====================
# Company
# =====================
class Company(BaseModel, SoftDeleteMixin):
    __tablename__ = "company"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="company",passive_deletes=True
    )


# =====================
# Organization
# =====================
class Organization(BaseModel, SoftDeleteMixin):
    __tablename__ = "organization"
    __table_args__ = (
        UniqueConstraint("company_id", "org_code", name="uix_company_orgcode"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    company_id: Mapped[int] = mapped_column(ForeignKey("company.id",  ondelete="RESTRICT"))
    org_code: Mapped[str] = mapped_column(String(50), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organization.id"), nullable=True
    )

    level: Mapped[int] = mapped_column(default=1)

    company: Mapped["Company"] = relationship(
        back_populates="organizations",passive_deletes=True
    )
    users: Mapped[list["User"]] = relationship(
        back_populates="organization"
    )
    task_access: Mapped[list["TaskAccessOrganization"]] = relationship(
        back_populates="organization"
    )
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'org_code': self.org_code,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'parent_id': self.parent_id,
            'level': self.level
        }
# =====================
# User
# =====================
class User(BaseModel, UserMixin, SoftDeleteMixin):
    __table_args__ = (
        UniqueConstraint("normalized_email", "is_deleted"),
        UniqueConstraint("wp_user_id", "is_deleted"),
    )
    wp_user_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(255), index=True)

    password_hash: Mapped[Optional[str]] = mapped_column(String(255))

    is_superuser: Mapped[bool] = mapped_column(default=False)

    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organization.id")
    )

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")

    access_scopes: Mapped[list["AccessScope"]] = relationship(
        lazy="select", overlaps="user"
    )

    task_orders: Mapped[list["UserTaskOrder"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    created_tasks: Mapped[list["Task"]] = relationship(
        back_populates="creator"
    )
    task_access: Mapped[list["TaskAccessUser"]] = relationship(
        back_populates="user"
    )
    password_reset_token_hash: Mapped[Optional[str]] = mapped_column(String(64))
    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    password_reset_used: Mapped[bool] = mapped_column(Boolean, default=False)

    @hybrid_property
    def company_id(self) -> Optional[int]:  # type: ignore[no-redef]
        return self.organization.company_id if self.organization else None

    @company_id.expression
    def company_id(cls):
        return select(Organization.company_id).where(
            Organization.id == cls.organization_id
        ).scalar_subquery()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def _normalize(e: str) -> str:
        return (e or "").strip().lower()

    @validates("email")
    def _on_email_set(self, key:str, value: str) -> str:
        self.normalized_email = self._normalize(value)
        return value


# =====================
# AccessScope
# =====================
class AccessScope(BaseModel):
    __tablename__ = "access_scope"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))

    role: Mapped[OrgRoleEnum] = mapped_column(IntEnumType(OrgRoleEnum))

    user: Mapped["User"] = relationship(overlaps="access_scopes",passive_deletes=True)
    organization: Mapped["Organization"] = relationship(overlaps="access_scopes")
# =====================
# Task
# =====================
class Task(BaseModel, SoftDeleteMixin):
    __tablename__ = "task"
    status: Mapped[StatusEnum] = mapped_column(
        IntEnumType(StatusEnum),
        default=StatusEnum.UNDEFINED
    )

    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    due_date: Mapped[Optional[date]] = mapped_column(Date)

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    display_order: Mapped[Optional[int]] = mapped_column() # NOT USE

    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organization.id")
    )

    creator: Mapped[Optional["User"]] = relationship(
        foreign_keys=[created_by],
        back_populates="created_tasks"
    )

    objective: Mapped[list["Objective"]] = relationship(
        back_populates="task"
    )
    user_access: Mapped[list["TaskAccessUser"]] = relationship(
        back_populates="task"
    )
    org_access: Mapped[list["TaskAccessOrganization"]] = relationship(
        back_populates="task"
    )
    user_orders: Mapped[list["UserTaskOrder"]] = relationship(
        back_populates="task"
    )
# =====================
# Objective
# =====================
class Objective(BaseModel, SoftDeleteMixin):
    __tablename__ = "objective"

    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))

    task: Mapped["Task"] = relationship(back_populates="objective")

    title: Mapped[Optional[str]] = mapped_column(String(255))
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    assigned_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))

    display_order: Mapped[int] = mapped_column(default=0)

    status: Mapped[StatusEnum] = mapped_column(
        IntEnumType(StatusEnum),
        default=StatusEnum.UNDEFINED
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    progress_update: Mapped[list["ProgressUpdate"]] = relationship(
        back_populates="objective"
    )
    reminder_settings: Mapped[list["ObjectiveReminderSetting"]] = relationship(
        back_populates="objective"
    )

# =====================
# ProgressUpdate
# =====================
class ProgressUpdate(BaseModel, SoftDeleteMixin):
    __tablename__ = "progress_update"

    objective_id: Mapped[int] = mapped_column(ForeignKey("objective.id"))
    objective: Mapped["Objective"] = relationship(
        back_populates="progress_update"
    )
    status: Mapped[StatusEnum] = mapped_column(
        IntEnumType(StatusEnum),
        default=StatusEnum.UNDEFINED
    )
    detail: Mapped[Optional[str]] = mapped_column(Text)
    report_date: Mapped[Optional[date]] = mapped_column(Date)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
# =====================
# ACCESS CONTROL
# =====================
class GroupScopeType(IntEnum):
    PRIVATE = 1       # 自分だけ
    ORGANIZATION = 2  # 組織内
    GLOBAL = 3        # 全体
class AccessSubjectType(IntEnum):
    USER = auto()
    ORGANIZATION = auto()
    GROUP = auto()
class AccessSubject(BaseModel):
    __tablename__ = "access_subject"
    __table_args__ = (
        UniqueConstraint("subject_type", "ref_id", name="uq_subject_type_ref_id"),
    )

    subject_type: Mapped[AccessSubjectType] = mapped_column(IntEnumType(AccessSubjectType))
    ref_id: Mapped[int] = mapped_column()  # user_id / organization_id / group_id
class TaskAccess(BaseModel):
    __tablename__ = "task_access"
    __table_args__ = (
        UniqueConstraint("task_id", "subject_id", name="uq_task_subject"),
    )
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id", ondelete="CASCADE"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("access_subject.id", ondelete="CASCADE"))

    access_level: Mapped[TaskAccessLevelEnum] = mapped_column(IntEnumType(TaskAccessLevelEnum))
class Group(BaseModel, SoftDeleteMixin):
    __tablename__ = "group"

    name: Mapped[str]= mapped_column(String(255))

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    members: Mapped[list["GroupMember"]] = relationship(back_populates="group")
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organization.id"))
    

    scope_type: Mapped[GroupScopeType] = mapped_column(IntEnumType(GroupScopeType))
class GroupMember(BaseModel):
    __tablename__ = "group_member"

    group_id: Mapped[int] = mapped_column(ForeignKey("group.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    group: Mapped["Group"] = relationship(back_populates="members")
class TaskAccessUser(BaseModel):
    __tablename__ = 'task_access_user'
    task_id:Mapped[int] = mapped_column(ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id:Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    access_level: Mapped[TaskAccessLevelEnum] = mapped_column(IntEnumType(TaskAccessLevelEnum), nullable=False, default=TaskAccessLevelEnum.VIEW)
    task: Mapped["Task"] = relationship(
        back_populates="user_access"
    )
    user: Mapped["User"] = relationship(
        back_populates="task_access"
    )

class TaskAccessOrganization(BaseModel):
    __tablename__ = 'task_access_organization'
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    access_level: Mapped[TaskAccessLevelEnum] = mapped_column(IntEnumType(TaskAccessLevelEnum), nullable=False, default=TaskAccessLevelEnum.VIEW)
    task: Mapped["Task"] = relationship(
        back_populates="org_access"
    )
    organization: Mapped["Organization"] = relationship(
        back_populates="task_access"
    )

class UserTaskOrder(BaseModel):
    __tablename__ = 'user_task_order'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'task_id', name='uix_user_task'),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    display_order: Mapped[int] = mapped_column(db.Integer, nullable=False)
    task: Mapped["Task"] = relationship(
        back_populates="user_orders"
    )
    user: Mapped["User"] = relationship('User', back_populates='task_orders')

class ObjectiveReminderSetting(BaseModel):
    __tablename__ = "objective_reminder_settings"
    __table_args__ = (
        db.Index("ix_reminder_active_objective", "objective_id", "is_active"),
        db.Index("ix_reminder_condition", "condition_type"),
    )
    objective_id: Mapped[int] = mapped_column(ForeignKey("objective.id", ondelete="CASCADE"), nullable=False)

    condition_type: Mapped[ReminderConditionEnum] = mapped_column(IntEnumType(ReminderConditionEnum), nullable=False)
    threshold_days: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    frequency_type: Mapped[ReminderFrequencyEnum] = mapped_column(IntEnumType(ReminderFrequencyEnum), nullable=False)
    interval_days: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    send_time_local: Mapped[time] = mapped_column(db.Time, nullable=False, default=time(9, 0, 0))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    objective: Mapped["Objective"] = relationship(
        back_populates="reminder_settings"
    )



class ObjectiveReminderLog(BaseModel):
    __tablename__ = "objective_reminder_logs"
    __table_args__ = (
        db.Index("ix_reminder_log_objective_time", "objective_id", "sent_at"),
        db.Index("ix_reminder_log_user_time", "user_id", "sent_at"),
    )
    setting_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("objective_reminder_settings.id"), nullable=False)
    objective_id: Mapped[int] = mapped_column(ForeignKey("objective.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    condition_type: Mapped[ReminderConditionEnum] = mapped_column(IntEnumType(ReminderConditionEnum), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(db.String(16), nullable=False)  # SUCCESS / FAILURE
    error_message: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)

