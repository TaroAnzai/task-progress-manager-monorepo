// src/acl/policy.ts
export type AccessLevel = 'VIEW' | 'EDIT' | 'FULL';

export type Action =
  | 'task.view' | 'task.create' | 'task.update' | 'task.delete'
  | 'objective.view' | 'objective.create' | 'objective.update' | 'objective.delete'
  | 'progress.view' | 'progress.create' | 'progress.update' | 'progress.delete';

const levelRank = { VIEW: 1, EDIT: 2, FULL: 3 } as const;

const requiredLevel: Record<Action, AccessLevel> = {
  'task.view': 'VIEW',
  'task.create': 'FULL',
  'task.update': 'FULL',
  'task.delete': 'FULL',
  'objective.view': 'VIEW',
  'objective.create': 'EDIT',
  'objective.update': 'EDIT',
  'objective.delete': 'EDIT',
  'progress.view': 'VIEW',
  'progress.create': 'EDIT',   // ← 閲覧でも「担当者例外」を下で許可
  'progress.update': 'EDIT',   // ← 同上
  'progress.delete': 'FULL',
};

export const baseAllowed = (level: AccessLevel | undefined, action: Action) =>
  !!level && levelRank[level] >= levelRank[requiredLevel[action]];
