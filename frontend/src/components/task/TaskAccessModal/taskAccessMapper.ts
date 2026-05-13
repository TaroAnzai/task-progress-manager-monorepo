import type {
  AccessEntry,
  AccessLevelInput,
  TaskAccessResponse,
} from '@/api/generated/taskProgressAPI.schemas';

import type { AccessSubjectItem, TaskAccessItem } from './taskAccessTypes';

export const toTaskAccessItem = (apiItem: TaskAccessResponse): TaskAccessItem => ({
  subjectType: apiItem.subject_type,
  refId: apiItem.ref_id,
  name: apiItem.display_name ?? '(名称未設定)',
  accessLevel: apiItem.access_level,
});

export const toTaskAccessItems = (apiItems: TaskAccessResponse[]): TaskAccessItem[] =>
  apiItems.map(toTaskAccessItem);

export const toAccessEntry = (item: TaskAccessItem): AccessEntry => ({
  subject_type: item.subjectType,
  ref_id: item.refId,
  access_level: item.accessLevel,
});

export const toAccessLevelInput = (items: TaskAccessItem[]): AccessLevelInput => ({
  accesses: items.map(toAccessEntry),
});

export const toAccessSubjectItem = (apiItem: TaskAccessResponse): AccessSubjectItem => ({
  subjectType: apiItem.subject_type,
  refId: apiItem.ref_id,
  name: apiItem.display_name ?? '(名称未設定)',
});
