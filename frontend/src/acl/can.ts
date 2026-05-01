// src/acl/can.ts

import type { Objective, Task } from '@/api/generated/taskProgressAPI.schemas';

import { type AccessLevel, type Action, baseAllowed } from './policy';

type Subject = Task | Objective | { taskId: number };
const isTask = (s: Subject): s is Task => !('task_id' in s) && 'user_access_level' in s;
const isObjective = (s: Subject): s is Objective => 'task_id' in s;

const extractTaskId = (s: Subject): number => {
  if ('taskId' in s) return s.taskId;
  if (isObjective(s)) return s.task_id;
  if (isTask(s)) return s.id;
  throw new Error(`Unsupported subject: ${JSON.stringify(s)}`);
};

/** ← ココがポイント：Objective から assigned_user_id を直参照 */
const isAssignedToUser = (s: Subject, currentUserId?: number): boolean | undefined => {
  if (!isObjective(s) || currentUserId == null) return undefined;
  const assignedUserId = s.assigned_user_id ?? s.assigned_user_id;
  return Number(assignedUserId) === Number(currentUserId);
};

export type LevelResolver = (taskId: number) => AccessLevel | undefined;

export const can = (
  action: Action,
  subject: Subject,
  resolveLevel: LevelResolver,
  currentUserId?: number
): boolean => {
  const taskId = extractTaskId(subject);
  const level = resolveLevel(taskId);
  // 基本レベルで判定
  if (baseAllowed(level, action)) return true;

  // 閲覧権限でも担当者なら 進捗の作成・更新 を許可
  if ((action === 'progress.create' || action === 'progress.update') && level === 'VIEW') {
    if (isAssignedToUser(subject, currentUserId)) return true;
  }

  return false;
};
