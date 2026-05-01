import { useState } from 'react';

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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

import { usePostObjectives } from '@/api/generated/taskProgressAPI';
import type { ObjectiveItem } from '@/api/generated/taskProgressAPI.schemas';

import { extractErrorMessage } from '@/utils/errorHandler';

import { useTasks } from '@/context/useTasks';

import { AiSuggestModal } from '../aiSuggestModal/AiSuggestModal';

interface TaskSettingModalProps {
  open: boolean;
  onClose: () => void;
}

export const NewTaskModal = ({ open, onClose }: TaskSettingModalProps) => {
  const { createTask, createTaskAsync } = useTasks();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [openAiSuggestModal, setOpenAiSuggestModal] = useState(false);

  //新規登録関数
  const { mutate: postObjective } = usePostObjectives({
    mutation: {
      onSuccess: () => {
        toast.success('Objectiveを登録しました');
        //refetchObjectives();
      },
      onError: (e) => {
        const err = extractErrorMessage(e);
        console.error('Objective登録失敗:', err);
        toast.error('Objective登録に失敗しました', { description: err });
      },
    },
  });
  const clearForm = () => {
    setTitle('');
    setDescription('');
    setDueDate('');
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error('タイトルは必須です');
      return;
    }

    const payload = {
      title: title.trim(),
      description: description.trim(),
      due_date: dueDate || undefined,
    };
    createTask(payload);
    clearForm();
    onClose();
  };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSave();
    }
  };
  const handleAdaptAiSuggest = async (aiTitle: string, objectives: ObjectiveItem[]) => {
    setOpenAiSuggestModal(false);
    const payload = {
      title: aiTitle.trim(),
      description: description.trim(),
      due_date: dueDate || undefined,
    };
    const response = await createTaskAsync(payload);
    const taskId = response.task?.id;
    if (taskId) {
      objectives.map((objective) => postObjective({ data: { ...objective, task_id: taskId } }));
    }
    onClose();
  };
  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>"新規タスク作成"</DialogTitle>
            <DialogDescription></DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Textarea
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="タスク名"
              rows={1}
              className="h-auto min-h-0 resize-none overflow-hidden"
            />

            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="タスクの説明"
              className="h-auto min-h-0"
            />

            <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>
          <DialogFooter>
            <Button
              className="mr-auto"
              variant="secondary"
              onClick={() => setOpenAiSuggestModal(true)}
            >
              "AI提案"
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                clearForm();
                onClose();
              }}
            >
              キャンセル
            </Button>
            <Button onClick={handleSave}>"作成"</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {openAiSuggestModal && (
        <AiSuggestModal
          title={title}
          discription={description}
          dueDate={dueDate}
          open={openAiSuggestModal}
          onClose={() => {
            setOpenAiSuggestModal(false);
          }}
          onAdapt={handleAdaptAiSuggest}
        />
      )}
    </>
  );
};
