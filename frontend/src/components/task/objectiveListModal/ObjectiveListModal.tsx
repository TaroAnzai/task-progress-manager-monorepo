//src\components\task\taskSettingOrderModal\TaskOrderSettingModal.tsx
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import {
  getGetObjectivesTasksTaskIdQueryOptions,
  useDeleteObjectivesObjectiveId,
  useGetObjectivesTasksTaskId,
  usePutObjectivesObjectiveId,
} from '@/api/generated/taskProgressAPI';
import type {
  Objective,
  ObjectiveUpdateStatus as updateStatusType,
  Task,
} from '@/api/generated/taskProgressAPI.schemas';

import { useAlertDialog } from '@/context/useAlertDialog';

import { StatusBadgeCell } from '../StatusBadgeCell';
interface ObjectiveListModalProps {
  open: boolean;
  task: Task;
  canUpdate: boolean;
  onClose: () => void;
}

export const ObjectiveListModal = ({ open, task, canUpdate, onClose }: ObjectiveListModalProps) => {
  const qc = useQueryClient();
  const { openAlertDialog } = useAlertDialog();

  const { data } = useGetObjectivesTasksTaskId(task.id);
  const { mutate: updateObjective } = usePutObjectivesObjectiveId({
    mutation: {
      onSuccess: () => {
        toast.success('オブジェクティブを更新しました');
        const { queryKey } = getGetObjectivesTasksTaskIdQueryOptions(task.id);
        qc.invalidateQueries({ queryKey });
      },
      onError: (error) => {
        openAlertDialog({
          title: 'Error',
          description: error,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
    },
  });
  const { mutate: deleteObjective } = useDeleteObjectivesObjectiveId({
    mutation: {
      onSuccess: () => {
        toast.success('オブジェクティブを削除しました');
        const { queryKey } = getGetObjectivesTasksTaskIdQueryOptions(task.id);
        qc.invalidateQueries({ queryKey });
      },
      onError: (error) => {
        openAlertDialog({
          title: 'Error',
          description: error,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
    },
  });
  const handleUpdateTaskStatus = (objId: number, newStatus: updateStatusType) => {
    updateObjective({ objectiveId: objId, data: { status: newStatus } });
  };
  const handleDeleteObjective = (objective_id: number) => {
    deleteObjective({ objectiveId: objective_id });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>オブジェクティブの一覧 </DialogTitle>
          <DialogDescription> ステータス変更と完全削除 </DialogDescription>
        </DialogHeader>
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-white">
            <TableRow>
              <TableHead className="px-3 py-2">オブジェクティブ</TableHead>
              <TableHead className="w-[100px] text-center px-3 py-2">期限</TableHead>
              <TableHead className="w-[100px] text-center px-3 py-2">ステータス</TableHead>
              <TableHead className="w-[100px] text-center px-3 py-2">担当者</TableHead>
              <TableHead className="w-[70px] text-center px-3 py-2">削除</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.objectives?.map((obj: Objective) => (
              <TableRow key={obj.id}>
                <TableCell className="font-medium">{obj.title}</TableCell>
                <TableCell className="text-center">{obj.due_date}</TableCell>
                <TableCell className="text-center">
                  <StatusBadgeCell
                    value={obj.status}
                    disabled={!canUpdate}
                    onChange={(newStatus) => {
                      handleUpdateTaskStatus(obj.id, newStatus);
                    }}
                  />
                </TableCell>
                <TableCell className="text-center">{obj.assigned_user_name}</TableCell>
                <TableCell className="text-center">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteObjective(obj.id)}
                    disabled={!canUpdate}
                  >
                    削除
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <DialogFooter>
          <Button onClick={onClose}>閉じる</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
