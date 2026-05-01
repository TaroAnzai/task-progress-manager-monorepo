from marshmallow import Schema, fields, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Task
from app.constants import StatusEnum, TaskAccessLevelEnum
from app import db
from flask_login import current_user

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
        include_fk = True
        exclude = ("is_deleted",)
    id = fields.Integer(required=True, dump_only=True, allow_none=False)
    user_access_level = fields.Enum(TaskAccessLevelEnum,by_value=False, dump_only=True,
                                    metadata={"type":"string", "enum":[e.name for e in TaskAccessLevelEnum], "description":"タスクの権限"})
    status =  fields.Enum(StatusEnum, by_value=False, dump_only=True ,
                       metadata={"type": "string", "enum": [e.name for e in StatusEnum]})
    create_user_name = fields.Method("get_creator_name", dump_only=True,metadata={"type": "string", "description": "タスク作成者の名前"}) 
    has_assigned_objective = fields.Method("get_has_assigned_objective", dump_only=True, metadata={"type":"boolean", "description": "オブジェクティブにアサインされているか"})

    def get_has_assigned_objective(self, obj):
        # obj.objectives が eager load 済み
        return any(
            objv.assigned_user_id is not None and not objv.is_deleted
            for objv in getattr(obj, "objectives", [])
        )

    def get_creator_name(self, obj):
        return obj.creator.name if getattr(obj, "creator", None) else None

class TaskInputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = False
        include_fk = True
        exclude = ("id", "created_by", "created_at", "is_deleted")

    title = fields.Str(required=True)
    description = fields.Str(load_default="")
    due_date = fields.Str(load_default=None)
    status =  fields.Enum(StatusEnum, by_value=False, load_default=StatusEnum.UNDEFINED,
                       metadata={"type": "string", "enum": [e.name for e in StatusEnum]})
    display_order = fields.Int(load_default=None)



class TaskUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = False
        include_fk = True
        exclude = ("id", "created_by", "created_at", "is_deleted")

    title = fields.Str(required=False)
    description = fields.Str()
    due_date = fields.Str()
    status =  fields.Enum(StatusEnum, by_value=False,
                       metadata={"type": "string", "enum": [e.name for e in StatusEnum]})
    display_order = fields.Int()

class TaskCreateResponseSchema(Schema):
    message = fields.Str()
    task = fields.Nested(TaskSchema)

class TaskListResponseSchema(Schema):
    tasks = fields.List(fields.Nested(TaskSchema))

class OrderSchema(Schema):
    order = fields.List(fields.Int(), required=True)

class TaskOrderSchema(Schema):
    task_id = fields.Int()
    title = fields.Str()

class TaskOrderInputSchema(Schema):
    task_ids = fields.List(fields.Int(), required=True)
    user_id = fields.Int(required=True)

class StatusSchema(Schema):
    id = fields.Int()
    enum = fields.Str()
    label = fields.Str()