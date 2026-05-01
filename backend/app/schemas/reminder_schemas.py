# app/schemas/reminder_schemas.py
from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import ObjectiveReminderSetting, ObjectiveReminderLog
from app.reminder_constants import ReminderConditionEnum, ReminderFrequencyEnum

COND_VALUES = [e.name for e in ReminderConditionEnum]
FREQ_VALUES = [e.name for e in ReminderFrequencyEnum]

# ---- Output -----------------------------------------------------------------

class ObjectiveReminderSettingSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectiveReminderSetting
        load_instance = True
        include_fk = True
    condition_type = fields.Enum(
        ReminderConditionEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": COND_VALUES, "description": "NO_UPDATE / OVERDUE"}
    )
    frequency_type = fields.Enum(
        ReminderFrequencyEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": FREQ_VALUES, "description": "ONCE / INTERVAL"}
    )
    # 出力専用
    id = fields.Integer(dump_only=True, required=True, allow_none=False)

# ---- Create -----------------------------------------------------------------
class ObjectiveReminderSettingInputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectiveReminderSetting
        load_instance = False
        include_fk = True
        exclude = ("id", "objective_id","last_sent_at","created_at", "updated_at","objective")

    condition_type = fields.Enum(
        ReminderConditionEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": COND_VALUES, "description": "NO_UPDATE / OVERDUE"}
    )
    frequency_type = fields.Enum(
        ReminderFrequencyEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": FREQ_VALUES, "description": "ONCE / INTERVAL"}
    )
# ---- Update -----------------------------------------------------------------

class ObjectiveReminderSettingUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectiveReminderSetting
        load_instance = False
        include_fk = True
        exclude = ("id", "objective_id","last_sent_at","created_at", "updated_at","objective")

    condition_type = fields.Enum(
        ReminderConditionEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": COND_VALUES, "description": "NO_UPDATE / OVERDUE"}
    )
    frequency_type = fields.Enum(
        ReminderFrequencyEnum, by_value=False, required=True,
        metadata={"type": "string", "enum": FREQ_VALUES, "description": "ONCE / INTERVAL"}
    )

class ObjectiveReminderSettingListOutputSchema(Schema):
    items = fields.List(fields.Nested(ObjectiveReminderSettingSchema), required=True)
    total = fields.Integer(required=True)
    page = fields.Integer(required=False)
    per_page = fields.Integer(required=False)

# ---- （任意）ログ出力 --------------------------------------------------------

class ObjectiveReminderLogOutputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectiveReminderLog
        load_instance = True
        include_fk = True

    # condition_type は同様に Enum として出す
    condition_type = fields.Enum(
        ReminderConditionEnum, by_value=False, dump_only=True, required=True,
        metadata={"type": "string", "enum": COND_VALUES, "description": "NO_UPDATE / OVERDUE"}
    )
    status = fields.String(validate=validate.OneOf(["SUCCESS", "FAILURE"]))
