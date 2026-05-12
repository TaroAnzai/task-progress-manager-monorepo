from marshmallow import Schema, fields
from app.constants import TaskAccessLevelEnum
from app.models import AccessSubjectType

class AuthorizedUserSchema(Schema):
    user_id = fields.Integer(dump_only=True, required=True, allow_none=False)
    name = fields.Str(dump_only=True, required=True, allow_none=False)
    
class AccessEntrySchema(Schema):
    subject_type = fields.Enum(AccessSubjectType,required=True,
        metadata={"description": "アクセス対象種別", "example": "USER"}
    )
    ref_id = fields.Int(required=True,
        metadata={"description": "対象ID","example": 10}
    )
    access_level = fields.Enum(TaskAccessLevelEnum,required=True,
        metadata={"description": "アクセスレベル", "example": "EDIT"}
    )


class AccessLevelInputSchema(Schema):
    accesses = fields.List(fields.Nested(AccessEntrySchema), required=True,
                            metadata={"description": "アクセス設定一覧"}                       
    )

class TaskAccessResponseSchema(Schema):
    id = fields.Int(required=True, metadata={
            "description": "TaskAccess ID", "example": 1,},
    )
    subject_id = fields.Int(required=True, metadata={
            "description": "AccessSubject ID", "example": 10,},
    )
    subject_type = fields.Enum(AccessSubjectType, required=True, metadata={
            "description": "アクセス対象種別", "example": "USER",},
    )
    ref_id = fields.Int(required=True, metadata={
            "description": "対象ID。USERならuser_id、ORGANIZATIONならorganization_id、GROUPならgroup_id",
            "example": 3,
        },
    )
    access_level = fields.Enum(TaskAccessLevelEnum, required=True, metadata={
            "description": "アクセスレベル", "example": "EDIT",},
    )
    display_name = fields.Str(allow_none=True, metadata={
            "description": "画面表示用の名称。USERならユーザー名、ORGANIZATIONなら組織名、GROUPならグループ名",
            "example": "営業チームA",
        },
    )


class TaskAccessListResponseSchema(Schema):
    accesses = fields.List(
        fields.Nested(TaskAccessResponseSchema),
        required=True,
        metadata={
            "description": "タスクに設定されているアクセス一覧",
        },
    )
    


