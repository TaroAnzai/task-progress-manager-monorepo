# app/constants/reminder_constants.py
from enum import IntEnum

class ReminderConditionEnum(IntEnum):
    NO_UPDATE = 1
    OVERDUE  = 2

REMINDER_CONDITION_LABEL = {
    ReminderConditionEnum.NO_UPDATE : "NO_UPDATE",   # 進捗がX日更新されていない
    ReminderConditionEnum.OVERDUE : "OVERDUE",       # 期限超過&未完了
}

class ReminderFrequencyEnum(IntEnum):
    ONCE     = 1
    INTERVAL = 2

REMINDER_FREQUENCY_LABEL={
    ReminderFrequencyEnum.ONCE : "ONCE",             # 1回のみ
    ReminderFrequencyEnum.INTERVAL : "INTERVAL",
}     # X日間隔




