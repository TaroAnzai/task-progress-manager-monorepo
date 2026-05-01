import { useEffect, useRef, useState } from 'react';

import { ClockLoader } from 'react-spinners';
import TextareaAutosize from 'react-textarea-autosize';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table';

import { type AISuggestInput, type ObjectiveItem } from '@/api/generated/taskProgressAPI.schemas';

import { useAiResultPolling, useCreateAiSuggestJob } from './AiSuggestHooks';
interface AiSuggestModalProps {
  title: string;
  discription: string;
  dueDate: string;
  open: boolean;
  onClose: () => void;
  onAdapt: (title: string, objectives: ObjectiveItem[]) => void;
}

export const AiSuggestModal = ({
  title,
  discription,
  dueDate,
  open,
  onClose,
  onAdapt,
}: AiSuggestModalProps) => {
  const [titleJobId, settTitleJobId] = useState<string | null>(null);
  const [objectiveJobId, setObjectiveJobId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newObjectives, setNewObjectives] = useState<ObjectiveItem[] | null>(null);
  const createJob = useCreateAiSuggestJob();
  const { data: taskTileData } = useAiResultPolling(titleJobId);
  const { data: objectiveData } = useAiResultPolling(objectiveJobId);
  const hasTitleExecutedRef = useRef(false);
  const hasObjectiveExecutedRef = useRef(false);

  //Making title by AI
  useEffect(() => {
    if (!open) {
      setNewTitle('');
      hasTitleExecutedRef.current = false;
      return;
    }
    if (hasTitleExecutedRef.current) return;
    hasTitleExecutedRef.current = true;

    const payload: AISuggestInput = {
      task_info: {
        title: title,
        description: discription,
        deadline: dueDate,
      },
      mode: 'task_name',
    };
    (async () => {
      const makeTitleJobId = await createJob(payload);
      settTitleJobId(makeTitleJobId);
    })();
  }, [open, title, discription, dueDate, createJob]);

  useEffect(() => {
    if (!taskTileData?.task_title_data) return;
    const resTitle = taskTileData.task_title_data.title;
    setNewTitle(resTitle);
    settTitleJobId(null);
  }, [taskTileData]);

  //Making objective by AI
  useEffect(() => {
    if (!open) {
      setNewObjectives(null);
      hasObjectiveExecutedRef.current = false;
      return;
    }
    if (hasObjectiveExecutedRef.current) return;
    hasObjectiveExecutedRef.current = true;
    const objPayload: AISuggestInput = {
      task_info: {
        title: newTitle,
        description: discription,
        deadline: dueDate,
      },
      mode: 'objectives',
    };
    (async () => {
      const makeObjJobId = await createJob(objPayload);
      setObjectiveJobId(makeObjJobId);
    })();
  }, [open, newTitle, discription, dueDate, createJob]);
  useEffect(() => {
    if (!objectiveData?.objectives_data?.objectives) return;
    const resObjectives = objectiveData.objectives_data.objectives;
    setNewObjectives(resObjectives);
    setObjectiveJobId(null);
  }, [objectiveData]);
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>"AI提案作成"</DialogTitle>
          <DialogDescription></DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {!newTitle ? (
            <div className="flex justify-center items-center h-40">
              <ClockLoader size={30} color="blue" />
            </div>
          ) : (
            <TextareaAutosize
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="タスク名"
              className="w-full resize-none overflow-hidden rounded-md border p-2"
              minRows={1}
            />
          )}
        </div>
        {!newObjectives && newTitle ? (
          <div className="flex justify-center items-center h-40">
            <ClockLoader size={30} color="blue" />
          </div>
        ) : (
          <Table>
            <TableBody>
              {newObjectives?.map((o, index) => (
                <TableRow key={index}>
                  <TableCell>{o.title}</TableCell>
                  <TableCell>{o.due_date}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <DialogFooter>
          <Button
            className="mr-auto"
            variant="secondary"
            onClick={() => newObjectives && onAdapt(newTitle, newObjectives)}
            disabled={!newObjectives}
          >
            適用
          </Button>
          <Button onClick={onClose}>キャンセル</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
