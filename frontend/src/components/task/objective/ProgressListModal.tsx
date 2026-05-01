// src/components/task/taskSettingModal/TaskSettingModal.tsx
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

import { useGetUpdatesObjectiveId } from '@/api/generated/taskProgressAPI';
import type { Objective } from '@/api/generated/taskProgressAPI.schemas';

import { useTasks } from '@/context/useTasks';
interface ProgressListModalProps {
  open: boolean;
  objective: Objective;
  onClose: () => void;
  onDelete: (id: number) => void;
}

export const ProgressListModal = ({
  open,
  objective,
  onClose,
  onDelete,
}: ProgressListModalProps) => {
  const { data } = useGetUpdatesObjectiveId(objective?.id);
  const { can } = useTasks();

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>進捗一覧</DialogTitle>
          <DialogDescription></DialogDescription>
        </DialogHeader>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="">進捗</TableHead>
              <TableHead className="w-[100px] text-center">登録者</TableHead>
              <TableHead className="w-[100px] text-center">登録日</TableHead>
              <TableHead className="w-[70px] text-center">削除</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.map((update) => (
              <TableRow key={update.id}>
                <TableCell className="font-medium whitespace-pre-wrap">{update.detail}</TableCell>
                <TableCell className="text-center">{update.updated_by}</TableCell>
                <TableCell className="text-center">{update.report_date}</TableCell>
                <TableCell className="text-center">
                  {can('progress.delete', objective) && (
                    <Button variant="destructive" size="sm" onClick={() => onDelete(update.id)}>
                      削除
                    </Button>
                  )}
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
