from marshmallow import Schema, fields
from app.constants import TaskAccessLevelEnum

class AuthorizedUserSchema(Schema):
    user_id = fields.Integer(dump_only=True, required=True, allow_none=False)
    name = fields.Str(dump_only=True, required=True, allow_none=False)
    
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

class _AccessUserInputSchema(Schema):
    user_id = fields.Int(required=True)
    access_level =  fields.Enum(TaskAccessLevelEnum, by_value=False, required=True,
                             metadata={"type": "string", "enum": [e.name for e in TaskAccessLevelEnum]}
    )

class _AccessOrgInputSchema(Schema):
    organization_id = fields.Int(required=True)
    access_level =  fields.Enum(TaskAccessLevelEnum, by_value=False, required=True,
                             metadata={"type": "string", "enum": [e.name for e in TaskAccessLevelEnum]}
    )

class AccessLevelInputSchema(Schema):
    user_access = fields.List(fields.Nested(_AccessUserInputSchema), required=True)
    organization_access = fields.List(fields.Nested(_AccessOrgInputSchema), required=True)
