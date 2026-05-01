// src/components/task/ObjectiveTable.tsx

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { Skeleton } from '@/components/ui/skeleton';
import { TableHead, TableHeader, TableRow } from '@/components/ui/table';

import {
  getGetObjectivesTasksTaskIdQueryKey,
  useGetObjectivesTasksTaskId,
  usePostObjectives,
  usePostTasksTaskIdObjectivesOrder,
  usePutObjectivesObjectiveId,
} from '@/api/generated/taskProgressAPI';
import type {
  Objective,
  ObjectiveInput,
  ObjectivesList,
  ObjectiveUpdate,
} from '@/api/generated/taskProgressAPI.schemas';
import { ObjectiveStatus } from '@/api/generated/taskProgressAPI.schemas';

import {
  DraggableRow,
  DraggableTable,
  DraggableTableBody,
  DraggableTableHead,
} from '@/components/DraggableTable';

import { extractErrorMessage } from '@/utils/errorHandler';

import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';

import { NewObjectiveRow } from './objective/NewObjectiveRow';
import { ObjectiveRow } from './objective/ObjectiveRow';

interface ObjectiveTableProps {
  taskId: number;
}

export const ObjectiveTable = ({ taskId }: ObjectiveTableProps) => {
  const qc = useQueryClient();
  const { user } = useUser();
  const { can } = useTasks();
  const {
    data,
    isLoading,
    refetch: refetchObjectives,
  } = useGetObjectivesTasksTaskId(taskId);

  //新規登録関数
  const { mutate: postObjective } = usePostObjectives({
    mutation: {
      onSuccess: () => {
        toast.success('Objectiveを登録しました');
        refetchObjectives();
      },
      onError: (e) => {
        const err = extractErrorMessage(e);
        console.error('Objective登録失敗:', err);
        toast.error('Objective登録に失敗しました', { description: err });
      },
    },
  });
  const { mutate: updateObjective } = usePutObjectivesObjectiveId({
    mutation: {
      onMutate: async (variables) => {
        await qc.cancelQueries({ queryKey: getGetObjectivesTasksTaskIdQueryKey(taskId) });
        const previousData: ObjectivesList | undefined = qc.getQueryData(
          getGetObjectivesTasksTaskIdQueryKey(taskId)
        );
        if (!previousData?.objectives) return { previousData };
        //楽観的更新
        const optimisticObjectives: Objective[] = previousData.objectives.map((obj) =>
          obj.id === variables.objectiveId ? { ...obj, ...variables.data } : obj
        );
        if (!optimisticObjectives) return { previousData };
        qc.setQueryData(
          getGetObjectivesTasksTaskIdQueryKey(taskId),
          (old: ObjectivesList | undefined) =>
            old
              ? { ...old, objectives: optimisticObjectives }
              : { objectives: optimisticObjectives }
        );
        return { previousData };
      },
      onSuccess: () => {
        toast.success('Objectiveを更新しました');
        refetchObjectives();
      },
      onError: (e, _vars, context) => {
        const err = extractErrorMessage(e);
        console.error(`Objectiveの更新に失敗しました`, e);
        toast.error('Objective更新に失敗しました', { description: err });
        if (context?.previousData) {
          qc.setQueryData(
            getGetObjectivesTasksTaskIdQueryKey(taskId),
            context.previousData
          );
        }
      },
    },
  });

  // ✅ 並び順更新：楽観的更新を追加
  const { mutate: postObjectivesOrderMutation } = usePostTasksTaskIdObjectivesOrder({
    mutation: {
      // ドロップ直後に即UI反映
      onMutate: async (variables) => {
        const queryKey = getGetObjectivesTasksTaskIdQueryKey(taskId);
        await qc.cancelQueries({ queryKey });

        const previousData = qc.getQueryData<ObjectivesList | undefined>(queryKey);

        // 既存キャッシュが無ければ何もしない
        if (!previousData?.objectives) {
          return { previousData, queryKey };
        }

        // ① 既存オブジェクトをID→オブジェクトのMapに
        const byId = new Map(previousData.objectives.map((o) => [o.id, o]));

        // ② 受け取った order に従って並べ替え（存在しないIDは除外）
        const order = variables.data?.order ?? [];
        const reordered: Objective[] = order
          .map((id) => byId.get(id))
          .filter((o): o is Objective => !!o);

        // ③ 万一 order に含まれない要素があれば末尾に付ける（保険）
        if (reordered.length < previousData.objectives.length) {
          const missing = previousData.objectives.filter((o) => !order.includes(o.id));
          reordered.push(...missing);
        }

        // ④ キャッシュを ObjectivesList 形式で上書き（ここが重要！）
        qc.setQueryData(queryKey, (old: ObjectivesList | undefined) =>
          old ? { ...old, objectives: reordered } : { objectives: reordered }
        );

        // ロールバック用
        return { previousData, queryKey };
      },

      // 失敗時は元に戻す
      onError: (_err, _vars, ctx) => {
        if (ctx?.previousData) {
          qc.setQueryData(ctx.queryKey, ctx.previousData);
        }
        toast.error('順序更新に失敗しました');
      },

      // 成功時のトースト
      onSuccess: () => {
        toast.success('順序を更新しました');
      },

      // 最終的にサーバー真実と同期（UIは既に並び替わっている）
      onSettled: (_d, _e, _v, ctx) => {
        if (ctx?.queryKey) {
          qc.invalidateQueries({ queryKey: ctx.queryKey });
        }
      },
    },
  });

  //早期リターン
  if (!user) return;
  if (isLoading) {
    return <Skeleton className="h-16 w-full" />;
  }

  // Objective新規登録関数
  const handleSaveNew = async (obj: ObjectiveInput) => {
    if (!obj.title || !obj.title.trim()) {
      console.warn('タイトルが入力されていません');
      return;
    }
    postObjective({
      data: {
        title: obj.title.trim(),
        due_date: obj.due_date ?? null,
        assigned_user_id: obj.assigned_user_id ?? user.id,
        task_id: taskId,
      },
    });
  };

  //更新用ハンドル関数
  const handleUpdate = async (objId: number, updates: ObjectiveUpdate) => {
    if (!objId) {
      console.warn('無効なIDです');
      return;
    }
    // 空文字だけのタイトルは保存させない（任意）
    if (typeof updates.title === 'string' && updates.title.trim() === '') {
      console.warn('タイトルが空文字のため更新しません');
      return;
    }
    updateObjective({ objectiveId: objId, data: updates });
  };
  // ドロップ時の並べ替え
  const handleRender = (newObj: Objective[]) => {
    const newObjectives = newObj.map((o) => o.id);
    postObjectivesOrderMutation({ taskId: taskId, data: { order: newObjectives } });
  };
  if (!data?.objectives) return null;
  return (
    <div className="overflow-x-auto">
      <DraggableTable
        items={data.objectives}
        getId={(item) => item.id}
        useGrabHandle={true}
        onReorder={handleRender}
        className="min-w-full text-sm text-left"
      >
        <TableHeader className="bg-gray-100">
          <TableRow>
            <DraggableTableHead id="objective" className="w-[400px] px-3 py-2">
              オブジェクティブ
            </DraggableTableHead>
            <DraggableTableHead id="due_date" className="w-[120px] px-3 py-2">
              期限
            </DraggableTableHead>
            <DraggableTableHead id="status" className="w-[120px] px-3 py-2">
              ステータス
            </DraggableTableHead>
            <DraggableTableHead id="assigned_user" className="w-[120px] px-3 py-2">
              担当者
            </DraggableTableHead>
            <DraggableTableHead id="progress" className="px-3 py-2">
              進捗
            </DraggableTableHead>
            <TableHead className="w-[100px] px-3 py-2">報告日</TableHead>
            <TableHead className="w-[60px] px-3 py-2">履歴</TableHead>
            <TableHead className="w-[60px] px-3 py-2">Mail</TableHead>
          </TableRow>
        </TableHeader>
        <DraggableTableBody>
          {data.objectives
            .filter((task) => task.status !== ObjectiveStatus.SAVED)
            .map((obj) => (
              <DraggableRow
                key={obj.id}
                id={obj.id}
                disabled={!can('objective.update', { taskId: taskId })}
              >
                <ObjectiveRow taskId={taskId} objective={obj} onUpdate={handleUpdate} />
              </DraggableRow>
            ))}

          {/* 常に表示される新規入力行 */}
          {can('objective.create', { taskId: taskId }) && (
            <TableRow>
              <NewObjectiveRow key="new" taskId={taskId} onSaveNew={handleSaveNew} />
            </TableRow>
          )}
        </DraggableTableBody>
      </DraggableTable>
    </div>
  );
};
