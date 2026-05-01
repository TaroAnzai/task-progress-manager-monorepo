// src/components/task/TaskHeader.tsx
import { useMemo } from 'react';

import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

import type {
  Task,
  TaskUpdateStatus as TaskUpdateStatusType,
} from '@/api/generated/taskProgressAPI.schemas';

import { useTasks } from '@/context/useTasks';

import { StatusBadgeCell } from './StatusBadgeCell';
import { TaskSettingsIcon } from './TaskSettingsIcon';

interface TaskHeaderProps {
  task: Task;
}

export const TaskHeader = ({ task }: TaskHeaderProps) => {
  const { can, updateTask } = useTasks();
  const isUpdateTask = useMemo(() => can('task.update', task), [can, task]);

  const handleUpdateTaskStatus = (status: TaskUpdateStatusType) => {
    updateTask(task.id, { status: status });
  };

  const dueDateStr = task.due_date
    ? format(new Date(task.due_date), 'yyyy年M月d日', { locale: ja })
    : '期限未設定';

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:gap-4 w-full">
      <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2 flex-grow">
        <h4 className="md:w-[50%] text-base font-semibold leading-snug text-gray-800 whitespace-pre-wrap">
          {task.title}
        </h4>
        <span className="text-sm text-gray-500 mr-1 flex">
          [作成者:&nbsp;
          <span className="w-[90px] truncate overflow-hidden text-ellipsis whitespace-nowrap">
            {task.create_user_name}
          </span>
          ]
        </span>
        <span className="w-[150px] text-sm text-gray-500 whitespace-nowrap">
          [期限: {dueDateStr}]
        </span>
        <StatusBadgeCell
          value={task.status ?? 'UNDEFINED'}
          onChange={handleUpdateTaskStatus}
          disabled={!isUpdateTask}
        />
      </div>
      <div className="shrink-0">
        <TaskSettingsIcon task={task} isUpdateTask={isUpdateTask} />
      </div>
    </div>
  );
};
