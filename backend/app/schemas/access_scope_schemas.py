from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import AccessScope
from app.constants import OrgRoleEnum

class AccessScopeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AccessScope
        load_instance = True
        include_fk = True

    role =  fields.Enum(OrgRoleEnum, required=True,
        metadata={"type": "string", "enum": [e.name for e in OrgRoleEnum]}
    )

class AccessScopeInputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AccessScope
        load_instance = False
        include_fk = True
        exclude = ("id",)

    organization_id = fields.Int(required=True)
    role =  fields.Enum(OrgRoleEnum, required=True,
        metadata={"type": "string", "enum": [e.name for e in OrgRoleEnum]}
    )
