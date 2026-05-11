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
class AccessUserSchema(Schema):
    user_id = fields.Integer(dump_only=True, required=True, allow_none=False)
    name = fields.Str(dump_only=True, required=True, allow_none=False)
    access_level =  fields.Enum(TaskAccessLevelEnum, by_value=False, dump_only=True, required=True,
                             metadata={"type": "string", "enum": [e.name for e in TaskAccessLevelEnum]}
    )

class OrgAccessSchema(Schema):
    organization_id = fields.Integer(dump_only=True,required=True, allow_none=False)
    name = fields.Str(dump_only=True,required=True, allow_none=False)
    access_level =  fields.Enum(TaskAccessLevelEnum, by_value=False, dump_only=True, required=True,
                             metadata={"type": "string", "enum": [e.name for e in TaskAccessLevelEnum]}
    )

class AccessLevelInputSchema(Schema):
    accesses = fields.List(fields.Nested(AccessEntrySchema), required=True,
                            metadata={"description": "アクセス設定一覧"}                       
    )

class AccessLevelCreateSchema(Schema):
    user_id = fields.Integer(load_only=True, allow_none=True)
    organization_id = fields.Integer(load_only=True, allow_none=True)
    group_id = fields.Integer(load_only=True, allow_none=True)

    access_level = fields.Enum(TaskAccessLevelEnum, required=True)
    
class AccessLevelResponseSchema(Schema):
    subject_id = fields.Integer()
    subject_type = fields.Enum(AccessSubjectType)
    subject_name = fields.String()

    access_level = fields.Enum(TaskAccessLevelEnum)

class AccessLevelUpdateSchema(Schema):
    subject_id = fields.Integer(required=True)
    access_level = fields.Enum(TaskAccessLevelEnum, required=True)