from marshmallow import Schema, fields, validate

class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True, metadata={"description":"Mail Address :user@example.com"})

class PasswordResetConfirmSchema(Schema):
    token = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=8, error="Password must be at least 8 characters."),
        metadata={"description":"New Login Password"}
    )

class PasswordResetRequestMessageSchema(Schema):
    message = fields.String(required=True,  metadata={"description":"Message"})