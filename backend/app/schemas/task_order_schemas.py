from marshmallow import Schema, fields

class TaskOrderQuerySchema(Schema):
    user_id = fields.Int(
        required=True,
        metadata={"description": "タスク並び順を取得するユーザーのID"}
    )
