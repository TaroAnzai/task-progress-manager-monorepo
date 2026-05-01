import {
  ObjectiveReminderSettingConditionType,
  ObjectiveReminderSettingFrequencyType,
} from '@/api/generated/taskProgressAPI.schemas.ts';

export const REMINDER_CONDITION_LABELS: Record<ObjectiveReminderSettingConditionType, string> = {
  [ObjectiveReminderSettingConditionType.NO_UPDATE]: '未更新',
  [ObjectiveReminderSettingConditionType.OVERDUE]: '期限超過',
};
export const REMINDER_FREQUENCY_LABELS: Record<ObjectiveReminderSettingFrequencyType, string> = {
  [ObjectiveReminderSettingFrequencyType.ONCE]: '1回のみ',
  [ObjectiveReminderSettingFrequencyType.INTERVAL]: '繰り返し',
};
