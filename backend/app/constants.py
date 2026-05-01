from enum import IntEnum

class OrgRoleEnum(IntEnum):
    MEMBER = 1
    ORG_ADMIN = 2
    SYSTEM_ADMIN = 3

ORG_ROLE_LABELS = {
    OrgRoleEnum.MEMBER: "member",
    OrgRoleEnum.ORG_ADMIN: "org_admin",
    OrgRoleEnum.SYSTEM_ADMIN: "system_admin",
}

class TaskAccessLevelEnum(IntEnum):
    VIEW = 1
    EDIT = 2
    FULL = 3
    OWNER = 4

TASK_ACCESS_LABELS = {
    TaskAccessLevelEnum.VIEW: "view",
    TaskAccessLevelEnum.EDIT: "edit",
    TaskAccessLevelEnum.FULL: "full",
    TaskAccessLevelEnum.OWNER: "owner",
}

class StatusEnum(IntEnum):
    UNDEFINED = 0
    NOT_STARTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    SAVED = 4

STATUS_LABELS = {
    StatusEnum.UNDEFINED: "undefined",
    StatusEnum.NOT_STARTED: "not_started",
    StatusEnum.IN_PROGRESS: "in_progress",
    StatusEnum.COMPLETED: "completed",
    StatusEnum.SAVED: "saved",
}
