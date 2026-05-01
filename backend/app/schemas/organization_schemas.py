from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Organization

class OrganizationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Organization
        load_instance = True
        include_fk = True
        exclude = (
            "is_deleted",
        )
    id = fields.Integer(required=True, dump_only=True, allow_none=False)
    level = fields.Int()

class OrganizationInputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Organization
        load_instance = False
        include_fk = True
        exclude = ("id",)

    name = fields.Str(required=True)
    org_code = fields.Str(required=True)
    company_id = fields.Int(load_default=None)
    parent_id = fields.Int(load_default=None)

class OrganizationUpdateSchema(Schema):
    name = fields.Str()
    parent_id = fields.Int(allow_none=True)

class OrganizationTreeSchema(Schema):
    id = fields.Int(required=True)
    name = fields.Str(required=True)
    org_code = fields.Str(required=True)
    company_id = fields.Int(required=True)
    company_name = fields.Str(required=True)
    parent_id = fields.Int(allow_none=True)
    level = fields.Int()
    children = fields.List(fields.Nested(lambda: OrganizationTreeSchema()))

class OrganizationQuerySchema(Schema):
    company_id = fields.Int(metadata={"description": "会社ID"})