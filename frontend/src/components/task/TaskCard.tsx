// src/components/task/TaskCard.tsx

import { useEffect, useMemo, useState } from 'react';

import { Minus, Plus } from 'lucide-react';

import { useGetTasksTaskId } from '@/api/generated/taskProgressAPI';

import { ObjectiveTable } from './ObjectiveTable';
import { TaskHeader } from './TaskHeader';
interface TaskCardProps {
  taskId: number;
  isExpandParent?: boolean;
}

const storageKey = (id: number) => `objective_visibility_${id}`;
export const TaskCard = ({ taskId, isExpandParent }: TaskCardProps) => {
  const { data: task } = useGetTasksTaskId(taskId);
  const initial = useMemo(() => {
    const s = localStorage.getItem(storageKey(taskId));
    return s ? JSON.parse(s) : true;
  }, [taskId]);

  const toggle = () => setAndStore(!isExpand);

  const [isExpand, setIsExpand] = useState<boolean>(initial);
  const setAndStore = (v: boolean) => {
    setIsExpand(v);
    localStorage.setItem(storageKey(taskId), JSON.stringify(v));
  };

  useEffect(() => {
    if (typeof isExpandParent === 'boolean' && isExpand !== isExpandParent) {
      setAndStore(isExpandParent);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isExpandParent]);

  if (!task) return null;
  return (
    <div className="rounded-xl border border-gray-300 bg-white shadow-sm">
      <div className="flex items-start justify-between px-4 py-2 border-b">
        <TaskHeader task={task} />
        <div className="h-9 flex items-center">
          <button onClick={toggle} className="text-sm text-blue-600 hover:underline">
            {isExpand ? <Minus className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
          </button>
        </div>
      </div>
      <div className={`px-4 py-2" ${isExpand ? 'block' : 'hidden'}`}>
        <ObjectiveTable taskId={taskId} />
      </div>
    </div>
  );
};
