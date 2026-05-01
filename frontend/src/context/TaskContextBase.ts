import { createContext } from 'react';

import type {
  Objective,
  Task,
  TaskCreateResponse,
  TaskInput,
  TaskUpdate,
} from '@/api/generated/taskProgressAPI.schemas';

import type { AccessLevel, Action } from '@/acl/policy';
type Subject = Task | Objective | { taskId: number };
export interface TaskContextType {
  tasks: Task[];
  isLoading: boolean;
  createTask: (data: TaskInput) => void;
  createTaskAsync: (data: TaskInput) => Promise<TaskCreateResponse>;
  updateTask: (taskId: number, data: TaskUpdate) => void;
  deleteTask: (taskId: number) => void;
  updateTaskOrder: (task_ids: number[]) => void;
  refetch: () => void;
  levelOf: (taskId: number) => AccessLevel | undefined;
  can: (Action: Action, subject: Subject) => boolean; // ← 呼ぶ側は user.id 渡さなくてOK
  getDisabledProps: (
    action: Action,
    subject: Subject
  ) => { disabled: boolean; 'aria-disabled': boolean };
}

export const TaskContext = createContext<TaskContextType | undefined>(undefined);
