from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from .user_schemas import UserSchema

class LoginResponseSchema(Schema):
    message = fields.Str()
    user = fields.Nested(UserSchema)

class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)

class WPLoginSchema(Schema):
    wp_user_id = fields.Int(required=True)