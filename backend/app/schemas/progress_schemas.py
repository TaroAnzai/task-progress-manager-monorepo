from marshmallow import Schema, fields
from app.constants import StatusEnum

class ProgressInputSchema(Schema):
    status =  fields.Enum(StatusEnum, load_default=StatusEnum.UNDEFINED, required=False,
                       metadata={"type": "string", "enum": [e.name for e in StatusEnum]})
    detail = fields.Str(required=True)
    report_date = fields.DateTime(required=True)

class ProgressSchema(Schema):
    id = fields.Integer(required=True, dump_only=True, allow_none=False)
    status =  fields.Enum(StatusEnum, dump_only=True, metadata={"type": "string", "enum": [e.name for e in StatusEnum]})
    detail = fields.Str()
    report_date = fields.Date()
    updated_by =  fields.String()
