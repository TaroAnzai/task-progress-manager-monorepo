// src/components/task/taskSettingModal/hooks/useTaskEditModal.ts
import { useEffect, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  getGetTasksTaskIdQueryOptions,
  useGetTasksTaskIdAuthorizedUsers,
  usePutTasksTaskId,
} from '@/api/generated/taskProgressAPI';
import type { Task } from '@/api/generated/taskProgressAPI.schemas';

import { extractErrorMessage } from '@/utils/errorHandler';

import { useUser } from '@/context/useUser';
export const useTaskEditModal = (task: Task, onClose: () => void) => {
  const qc = useQueryClient();
  const { user } = useUser();

  const [formState, setFormState] = useState({
    title: task.title || '',
    description: task.description || '',
    due_date: task.due_date || '',
  });

  const [isEditable, setIsEditable] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const updateTask = usePutTasksTaskId();
  const { data: authorized_users } = useGetTasksTaskIdAuthorizedUsers(task.id);

  useEffect(() => {
    const editable = (authorized_users ?? []).some((u) => u.id === user?.id);
    setIsEditable(editable);
  }, [user, task, authorized_users]);

  const handleChange = (key: string, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!formState.title.trim()) {
      alert('タスク名は必須です');
      return;
    }
    const filteredData = Object.fromEntries(
      Object.entries({
        title: formState.title,
        description: formState.description,
        due_date: formState.due_date,
      }).filter(([, value]) => value != null && value !== '')
    );
    setIsSaving(true);
    try {
      await updateTask.mutateAsync({
        taskId: task.id,
        data: filteredData,
      });
      const { queryKey } = getGetTasksTaskIdQueryOptions(task.id);
      qc.invalidateQueries({ queryKey });
      onClose();

      toast.success('更新完了', { description: 'タスクを更新しました' });
    } catch (e) {
      const err = extractErrorMessage(e);
      console.error('タスク保存失敗', err);
      alert(`保存に失敗しました:${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  return {
    formState,
    isEditable,
    handleChange,
    handleSave,
    isSaving,
  };
};
