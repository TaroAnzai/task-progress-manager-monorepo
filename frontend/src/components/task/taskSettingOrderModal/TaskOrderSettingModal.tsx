//src\components\task\taskSettingOrderModal\TaskOrderSettingModal.tsx

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { TableCell } from '@/components/ui/table';

import type { Task, TaskUpdateStatus } from '@/api/generated/taskProgressAPI.schemas';

import { DraggableRow, DraggableTable, DraggableTableBody } from '@/components/DraggableTable';

import { SCOPE_LABELS } from '@/context/roleLabels';
import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';

import { StatusBadgeCell } from '../StatusBadgeCell';
interface TaskSettingModalProps {
  open: boolean;
  onClose: () => void;
}

export const TaskOrderSettingModal = ({ open, onClose }: TaskSettingModalProps) => {
  const { tasks, can, updateTask, deleteTask, updateTaskOrder } = useTasks();
  const { user } = useUser();
  const [lolalTasks, setLocalTasks] = useState<Task[]>(tasks);

  useEffect(() => {
    setLocalTasks(tasks);
  }, [tasks, setLocalTasks]);

  const handleUpdateTaskStatus = (task_id: number, status: TaskUpdateStatus) => {
    const payload = {
      status: status,
    };
    updateTask(task_id, payload);
  };

  const handleRender = (items: Task[]) => {
    if (!user) return;
    const newTasksArray = items.map((task) => task.id);
    setLocalTasks(items);
    updateTaskOrder(newTasksArray);
  };

  const handleDerete = (id: number) => {
    deleteTask(id);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>タスクの並び替え・削除 </DialogTitle>
          <DialogDescription> ドラッグしてタスク並び替・削除ボタンで削除 </DialogDescription>
        </DialogHeader>

        <DraggableTable
          items={lolalTasks ?? []}
          getId={(item) => item.id}
          useGrabHandle={true}
          onReorder={(newItems) => {
            if (!user) return;
            handleRender(newItems);
          }}
        >
          <DraggableTableBody>
            {lolalTasks?.map((task) => (
              <DraggableRow key={task.id} id={task.id}>
                <TableCell className="max-w-xs truncate">{task.title}</TableCell>
                <TableCell>{task.create_user_name}</TableCell>
                <TableCell className="text-center">{task.due_date}</TableCell>
                <TableCell className="text-center">
                  <StatusBadgeCell
                    value={task.status ?? 'UNDEFINED'}
                    onChange={(newStatus) => handleUpdateTaskStatus(task.id, newStatus)}
                    disabled={!can('task.update', task)}
                  />
                </TableCell>
                <TableCell className="text-center">
                  {task.user_access_level ? SCOPE_LABELS[task.user_access_level] : ''}
                </TableCell>
                <TableCell className="text-center">
                  {can('task.delete', task) && (
                    <Button variant="destructive" size="sm" onClick={() => handleDerete(task.id)}>
                      削除
                    </Button>
                  )}
                </TableCell>
              </DraggableRow>
            ))}
          </DraggableTableBody>
        </DraggableTable>

        <DialogFooter>
          <Button onClick={onClose}>閉じる</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
