// src/components/task/ObjectiveRow.tsx

import { useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { FileStack, Mail } from 'lucide-react';
import { toast } from 'sonner';

import { TableCell } from '@/components/ui/table';

import {
  getGetObjectivesTasksTaskIdQueryKey,
  getGetUpdatesObjectiveIdQueryOptions,
  useDeleteUpdatesProgressId,
  usePostUpdatesObjectiveId,
} from '@/api/generated/taskProgressAPI';
import type {
  Objective,
  ObjectivesList,
  ObjectiveUpdate,
  ObjectiveUpdateStatus as updateStatusType,
  ProgressInput,
} from '@/api/generated/taskProgressAPI.schemas';

import { useAlertDialog } from '@/context/useAlertDialog';
import { useTasks } from '@/context/useTasks';

import { ReminderSettingModal } from '../reminderSettingModal/ReminderSettingModal';
import { SingleUserSelectModal } from '../SingleUserSelectModal';
import { StatusBadgeCell } from '../StatusBadgeCell';

import { DateCell } from './DateCell';
import { EditableCell } from './EditableCell';
import { ProgressListModal } from './ProgressListModal';

interface ObjectiveRowProps {
  taskId: number;
  objective: Objective | null;
  onUpdate: (objId: number, updates: ObjectiveUpdate) => Promise<void>;
}

export const ObjectiveRow = ({ taskId, objective, onUpdate }: ObjectiveRowProps) => {
  const qc = useQueryClient();
  const { can } = useTasks();
  const [isUserSelectModalOpen, setIsUserSelectModalOpen] = useState(false);
  const [isProgressListModalOpen, setIsProgressListModalOpen] = useState(false);
  const [isRemainderSettingModalOpen, setIsRemainderSettingModalOpen] = useState(false);
  const { openAlertDialog } = useAlertDialog();

  const { mutate: postProgressMutation } = usePostUpdatesObjectiveId({
    mutation: {
      onMutate: async (variables) => {
        if (!objective) return;
        const queryKey = getGetObjectivesTasksTaskIdQueryKey(taskId);
        const prevData = qc.getQueryData(queryKey);
        const updatedData = {
          latest_progress: variables.data.detail,
          latest_report_date: '',
        };

        qc.setQueryData<ObjectivesList | undefined>(queryKey, (old) => {
          if (!old || !old.objectives) return;
          return {
            ...old,
            objectives: old.objectives.map((o) =>
              o.id === objective.id ? { ...o, ...updatedData } : o
            ),
          };
        });
        return { prevData };
      },
      onSuccess: () => {
        toast.success('進捗を更新しました');
      },
      onError: (err, _vars, context) => {
        const queryKey = getGetObjectivesTasksTaskIdQueryKey(taskId);
        qc.setQueryData(queryKey, context?.prevData);
        openAlertDialog({
          title: '進捗登録失敗',
          description: err,
          showCancel: false,
        });
      },
      onSettled: () => {
        qc.invalidateQueries({ queryKey: getGetObjectivesTasksTaskIdQueryKey(taskId) });
      },
    },
  });
  //進捗削除
  const { mutate: deleteProgressMutation } = useDeleteUpdatesProgressId({
    mutation: {
      onSuccess: () => {
        toast.success('進捗を削除しました');
        if (objective) {
          const { queryKey } = getGetUpdatesObjectiveIdQueryOptions(objective.id, {});
          qc.invalidateQueries({ queryKey });
        }
      },
      onError: () => {
        openAlertDialog({
          title: '進捗登録失敗',
          description: 'このデータを削除してもよろしいですか？',
          showCancel: false,
        });
      },
    },
  });
  const handleTitleSave = (newTitle: string) => {
    if (objective) {
      onUpdate(objective.id, { title: newTitle });
    }
  };

  const handleDateSave = (newDate: string | undefined) => {
    if (objective) {
      onUpdate(objective.id, { due_date: newDate });
    }
  };
  const handleStatusSave = (newStatus: updateStatusType) => {
    if (objective) {
      onUpdate(objective.id, { status: newStatus });
    }
  };
  const handleAssinedUserSave = (newUserId: number) => {
    if (objective) {
      onUpdate(objective.id, { assigned_user_id: newUserId });
    }
  };
  const handleProgressSave = (newProgress: string) => {
    if (newProgress === latest_progress || newProgress === '') {
      return false;
    }
    if (objective) {
      const data: ProgressInput = {
        detail: newProgress,
        report_date: new Date().toISOString(),
      };
      postProgressMutation({ objectiveId: objective.id, data: data });
    }
  };
  const handleProgressDelete = (progressId: number) => {
    if (objective) {
      deleteProgressMutation({ progressId: progressId });
    }
  };

  if (!objective) return null;
  const latest_progress = objective.latest_progress ?? '';
  const latest_report_date = objective.latest_report_date;
  const isCanUpdate = can('objective.update', objective);
  const isCanEditProgress = can('progress.update', objective);

  return (
    <>
      <TableCell className={`w-xl px-3 py-2 ${isCanUpdate ? '' : 'bg-gray-50 cursor-not-allowed'}`}>
        <EditableCell
          value={objective.title ?? ''}
          onSave={handleTitleSave}
          disabled={!isCanUpdate}
        />
      </TableCell>
      <TableCell className={`px-3 py-2 ${isCanUpdate ? '' : 'bg-gray-50 cursor-not-allowed'}`}>
        <DateCell
          value={objective.due_date ?? undefined}
          onSave={handleDateSave}
          disabled={!isCanUpdate}
          objective_id={objective?.id}
        />
      </TableCell>
      <TableCell className={`px-3 py-2 ${isCanUpdate ? '' : 'bg-gray-50 cursor-not-allowed'}`}>
        <StatusBadgeCell
          value={objective.status}
          onChange={handleStatusSave}
          disabled={!isCanUpdate}
        />
      </TableCell>
      <TableCell
        className={`px-3 py-2 ${isCanUpdate ? '' : 'bg-gray-50 cursor-not-allowed'}`}
        onClick={() => setIsUserSelectModalOpen(isCanUpdate)}
      >
        {objective?.assigned_user_name ?? '-'}
      </TableCell>
      <TableCell
        className={`px-3 py-2 ${isCanEditProgress ? '' : 'bg-gray-50 cursor-not-allowed'}`}
      >
        <EditableCell
          value={latest_progress}
          onSave={handleProgressSave}
          disabled={!isCanEditProgress}
        />
      </TableCell>
      <TableCell
        className={`px-3 py-2 ${isCanEditProgress ? '' : 'bg-gray-50 cursor-not-allowed'}`}
      >
        {latest_report_date}
      </TableCell>
      <TableCell className="px-3 py-2">
        <button
          className="text-blue-600 hover:underline text-xs"
          onClick={() => setIsProgressListModalOpen(true)}
        >
          <FileStack />
        </button>
      </TableCell>
      <TableCell className="px-3 py-2">
        <button
          className="text-blue-600 hover:underline text-xs"
          onClick={() => setIsRemainderSettingModalOpen(true)}
        >
          <Mail />
        </button>
      </TableCell>
      <SingleUserSelectModal
        taskId={taskId}
        open={isUserSelectModalOpen}
        onClose={() => setIsUserSelectModalOpen(false)}
        onConfirm={(newUserId) => {
          handleAssinedUserSave(newUserId.id);
        }}
      />
      {isProgressListModalOpen && (
        <ProgressListModal
          open={isProgressListModalOpen}
          objective={objective}
          onClose={() => {
            setIsProgressListModalOpen(false);
          }}
          onDelete={(objective_id) => {
            handleProgressDelete(objective_id);
          }}
        />
      )}
      {isRemainderSettingModalOpen && (
        <ReminderSettingModal
          open={isRemainderSettingModalOpen}
          objective_id={objective.id}
          onClose={() => {
            setIsRemainderSettingModalOpen(false);
          }}
        />
      )}
    </>
  );
};
