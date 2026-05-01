// src/components/task/taskSettingModal/TaskSettingModal.tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import type { Task } from "@/api/generated/taskProgressAPI.schemas";

import { useTaskEditModal } from "./hooks/useTaskEditModal";
import { SaveButton } from "./SaveButton";
import { TaskEditForm } from "./TaskEditForm";
interface TaskSettingModalProps {
  open: boolean;
  task: Task;
  onClose: () => void;
}

export const TaskSettingModal = ({ open, task, onClose }: TaskSettingModalProps) => {
  const {
    formState,
    isEditable,
    handleChange,
    handleSave,
    isSaving,
  } = useTaskEditModal(task, onClose);


  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>タスクの編集</DialogTitle>
          <DialogDescription>タスクを編集します</DialogDescription>
        </DialogHeader>

        <TaskEditForm formState={formState} isEditable={isEditable} onChange={handleChange} />
        <DialogFooter>
          <SaveButton
            isEditable={isEditable}
            isSaving={isSaving}
            onSave={handleSave}
            onClose={onClose}
          />
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
