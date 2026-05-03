# ruff: noqa: F401
# pyright: reportUnusedImport=false
"""This module serves as a central point for importing all schema classes used in the application.
By importing all schemas here, we can simplify imports in other parts of the application and maintain a cleaner codebase.
　use like：from app.schemas import UserSchema
"""
from .common_schemas import MessageSchema, ErrorResponseSchema, YAMLResponseSchema, DeleteQuerySchema
from .task_schemas import (
    TaskSchema,
    TaskInputSchema,
    TaskUpdateSchema,
    TaskCreateResponseSchema,
    TaskListResponseSchema,
    OrderSchema,
    TaskOrderSchema,
    TaskOrderInputSchema,
    StatusSchema,
)
from .task_order_schemas import TaskOrderQuerySchema
from .user_schemas import (
    UserSchema,
    UserWithScopesSchema,
    UserSchemaForAdmin,
    UserInputSchema,
    UserUpdateSchema,
    UserCreateResponseSchema,
    UserByEmailQuerySchema,
    UserByWPIDQuerySchema,
    UserQuerySchema,
)
from .auth_schemas import(
    LoginResponseSchema,
    LoginSchema,
    WPLoginSchema,
)
from .auth_password_reset_schemas import(
    PasswordResetConfirmSchema,
    PasswordResetRequestMessageSchema,
    PasswordResetRequestSchema,
)
from .company_schemas import (
    CompanySchema,
    CompanyInputSchema, 
    CompanyQuerySchema,
)
from .organization_schemas import (
    OrganizationSchema,
    OrganizationInputSchema,
    OrganizationUpdateSchema,
    OrganizationTreeSchema,
    OrganizationQuerySchema,
)
from .objective_schemas import (
    ObjectiveSchema,
    ObjectiveInputSchema,
    ObjectiveUpdateSchema,
    ObjectiveResponseSchema,
    ObjectivesListSchema,
)
from .progress_schemas import ProgressSchema, ProgressInputSchema
from .access_scope_schemas import AccessScopeSchema, AccessScopeInputSchema
from .task_access_schemas import (
    AuthorizedUserSchema,
    AccessUserSchema,
    OrgAccessSchema,
    AccessLevelInputSchema,
)
from .ai_schemas import AISuggestInputSchema, JobIdSchema, AIResultSchema
from .reminder_schemas import (
     ObjectiveReminderSettingSchema,
     ObjectiveReminderSettingInputSchema,
     ObjectiveReminderSettingUpdateSchema,
     ObjectiveReminderSettingListOutputSchema,
     ObjectiveReminderLogOutputSchema
     )


