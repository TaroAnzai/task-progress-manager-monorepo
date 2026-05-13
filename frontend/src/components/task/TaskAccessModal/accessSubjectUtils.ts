import type { AccessSubjectItem, AccessSubjectType, TaskAccessItem } from './taskAccessTypes';

export const getSubjectKey = (item: Pick<AccessSubjectItem, 'subjectType' | 'refId'>) =>
  `${item.subjectType}:${item.refId}`;

export const getSubjectTypeLabel = (subjectType: AccessSubjectType) => {
  switch (subjectType) {
    case 'USER':
      return 'ユーザー';
    case 'ORGANIZATION':
      return '組織';
    case 'GROUP':
      return 'グループ';
    default:
      return subjectType;
  }
};

export const getSubjectIcon = (subjectType: AccessSubjectType) => {
  switch (subjectType) {
    case 'USER':
      return '👤';
    case 'ORGANIZATION':
      return '🏢';
    case 'GROUP':
      return '👥';
    default:
      return '●';
  }
};

export const isSameSubject = (
  a: Pick<AccessSubjectItem, 'subjectType' | 'refId'>,
  b: Pick<AccessSubjectItem, 'subjectType' | 'refId'>
) => a.subjectType === b.subjectType && a.refId === b.refId;

export const hasAccessItem = (
  items: TaskAccessItem[],
  subject: Pick<AccessSubjectItem, 'subjectType' | 'refId'>
) => items.some((item) => isSameSubject(item, subject));
