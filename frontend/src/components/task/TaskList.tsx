// src/components/task/TaskList.tsx

import { ClipLoader } from 'react-spinners';

import { useGetTaskOrders } from '@/api/generated/taskProgressAPI';
import { type Task, TaskStatus } from '@/api/generated/taskProgressAPI.schemas';

import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';
import type { FilterAccessLevel } from '@/pages/TaskPage';

import { TaskCard } from './TaskCard';
import type { PickedUser } from './ViewUserSelectModal/ViewUserSelectModal';

interface TaskListProps {
  isExpandParent?: boolean;
  viewMode: Record<FilterAccessLevel, boolean>;
  selectedUser: PickedUser | null;
}

export const TaskList = ({ isExpandParent, viewMode, selectedUser }: TaskListProps) => {
  const { tasks: taskList, isLoading } = useTasks();
  const { user } = useUser();

  const { data: taskOrder } = useGetTaskOrders(
    { user_id: selectedUser?.id ?? 0 },
    {
      query: { enabled: !!selectedUser },
    }
  );

  // Filter out tasks with status SAVED
  const tasks = taskList ? (taskList as Task[]) : [];
  const notSavedTasks = taskOrder
    ? taskOrder
        .map((task) => tasks.find((t) => t.id === task.task_id))
        .filter((task): task is Task => !!task && task.status !== TaskStatus.SAVED)
    : tasks.filter((task) => task.status !== TaskStatus.SAVED);

  // Further filter tasks based on user access level
  const filteredTasks = notSavedTasks.filter(
    (task) =>
      (task.user_access_level && viewMode[task.user_access_level]) ||
      (task.created_by === user?.id && viewMode['OWNER']) ||
      (task.has_assigned_objective && viewMode['ASSIGNED'])
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full w-full">
        <ClipLoader color="#36d7b7" size={100} />
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {filteredTasks.map((task) => (
        <TaskCard key={task.id} taskId={task.id} isExpandParent={isExpandParent} />
      ))}
    </div>
  );
};
