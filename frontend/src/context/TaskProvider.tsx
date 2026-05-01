import { type ReactNode, useCallback, useMemo } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  getGetTasksQueryOptions,
  getGetTasksTaskIdQueryOptions,
  useDeleteTasksTaskId,
  useGetTasks,
  usePostTaskOrders,
  usePostTasks,
  usePutTasksTaskId,
} from '@/api/generated/taskProgressAPI';
import {
  type Objective,
  type Task,
  type TaskInput,
  type TaskListResponse,
  type TaskUpdate,
  TaskUserAccessLevel,
} from '@/api/generated/taskProgressAPI.schemas';

import { can as rawCan, type LevelResolver } from '@/acl/can';
import type { AccessLevel, Action } from '@/acl/policy';
import { useAlertDialog } from '@/context/useAlertDialog';
import { useUser } from '@/context/useUser';

import { TaskContext } from './TaskContextBase';
type Subject = Task | Objective | { taskId: number };
export const TaskProvider = ({ children }: { children: ReactNode }) => {
  const qc = useQueryClient();
  const { user } = useUser();
  const currentUserId = user?.id;
  // const [isLoading, setIsLoading] = useState(true);
  // // ローディング
  // useEffect(() => {
  //   setIsLoading(loading || isFetching || !user?.id);
  // }, [loading, isFetching, user?.id]);

  const { openAlertDialog } = useAlertDialog();
  const {
    data,
    isLoading: loading,
    isFetching,
    refetch,
  } = useGetTasks<TaskListResponse>({
    query: { enabled: !!user?.id }, // ログイン後に実行
  });
  const tasks = useMemo(() => data?.tasks ?? [], [data]);
  const isLoading = loading || isFetching || !user?.id;
  //----------------------CREATE TASK----------------------
  const createTask = (data: TaskInput) => _createTask({ data: data });

  const createTaskAsync = (data: TaskInput) => _createTaskAsync({ data: data });

  const { mutate: _createTask, mutateAsync: _createTaskAsync } = usePostTasks({
    mutation: {
      onSuccess: (newTask) => {
        const _task = newTask.task;
        if (!_task) return;
        const task = { ..._task, user_access_level: TaskUserAccessLevel.FULL };
        toast.success('作成完了', { description: '新しいタスクを作成しました' });
        const queryKeyTasks = getGetTasksQueryOptions().queryKey;
        const queryKeyTask = getGetTasksTaskIdQueryOptions(task.id).queryKey;
        qc.setQueryData(queryKeyTask, task);
        qc.setQueryData<TaskListResponse | undefined>(queryKeyTasks, (old) => {
          if (!old || !old.tasks) return { tasks: [task] };
          return {
            ...old,
            tasks: [task, ...old.tasks],
          };
        });
      },
      onError: (err) => {
        openAlertDialog({
          title: 'タスク作成に失敗しました',
          description: err,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
      onSettled: () => {},
    },
  });
  //----------------------UPDATE TASK----------------------
  const updateTask = (taskId: number, data: TaskUpdate) => {
    _updateTask({ taskId: taskId, data: data });
  };
  const { mutate: _updateTask } = usePutTasksTaskId({
    mutation: {
      onMutate: (variables) => {
        const queryKeyTasks = getGetTasksQueryOptions().queryKey;
        const queryKeyTask = getGetTasksTaskIdQueryOptions(variables.taskId).queryKey;
        const prevTasks = qc.getQueryData(queryKeyTasks);
        const prevTask = qc.getQueryData(queryKeyTask);
        // 楽観的更新
        qc.setQueryData<Task>(queryKeyTask, (old) => (old ? { ...old, ...variables.data } : old));

        qc.setQueryData<TaskListResponse | undefined>(queryKeyTasks, (old) => {
          if (!old || !old.tasks) return old;
          return {
            ...old,
            tasks: old.tasks.map((t) =>
              t.id === variables.taskId ? { ...t, ...variables.data } : t
            ),
          };
        });

        return { prevTask, prevTasks };
      },
      onError: (err, vars, context) => {
        if (context?.prevTasks) {
          const queryKeyTasks = getGetTasksQueryOptions().queryKey;
          qc.setQueryData(queryKeyTasks, context.prevTasks);
        }
        if (context?.prevTask) {
          const queryKeyTask = getGetTasksTaskIdQueryOptions(vars.taskId).queryKey;
          qc.setQueryData(queryKeyTask, context.prevTask);
        }
        openAlertDialog({
          title: 'タスク更新に失敗しました',
          description: err,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
      onSuccess: () => {
        toast.success('ステータスを更新しました');
      },
      onSettled: () => {},
    },
  });
  //----------------------UPDATE TASK ORDER----------------------
  const updateTaskOrder = (task_ids: number[]) => {
    if (!user) return;
    _updateTaskOrder({ data: { task_ids: task_ids, user_id: user.id } });
  };
  const { mutate: _updateTaskOrder } = usePostTaskOrders({
    mutation: {
      onMutate: (variables) => {
        const queryKeyTasks = getGetTasksQueryOptions().queryKey;
        const prevTasks = qc.getQueryData(queryKeyTasks);
        // 楽観的更新
        qc.setQueryData<TaskListResponse | undefined>(queryKeyTasks, (old) => {
          if (!old || !old.tasks) return old;
          return {
            ...old,
            tasks: old.tasks
              .slice()
              .sort(
                (a, b) =>
                  variables.data.task_ids.indexOf(a.id) - variables.data.task_ids.indexOf(b.id)
              ),
          };
        });
        return { prevTasks };
      },
      onSuccess: () => {
        toast.success('順序を更新しました');
      },
      onError: (err, _vars, context) => {
        if (context?.prevTasks) {
          const queryKeyTasks = getGetTasksQueryOptions().queryKey;
          qc.setQueryData(queryKeyTasks, context.prevTasks);
        }
        openAlertDialog({
          title: 'タスク更新に失敗しました',
          description: err,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
    },
  });
  // ----------------------DELETE TASK----------------------
  const deleteTask = (taskId: number) => _deleteTask({ taskId: taskId });
  const { mutate: _deleteTask } = useDeleteTasksTaskId({
    mutation: {
      onMutate: (variables) => {
        const queryKeyTasks = getGetTasksQueryOptions().queryKey;
        const queryKeyTask = getGetTasksTaskIdQueryOptions(variables.taskId).queryKey;
        const prevTasks = qc.getQueryData(queryKeyTasks);
        const prevTask = qc.getQueryData(queryKeyTask);
        // 楽観的更新
        qc.removeQueries({ queryKey: queryKeyTask });
        qc.setQueryData<TaskListResponse | undefined>(queryKeyTasks, (old) => {
          if (!old || !old.tasks) return old;
          return {
            ...old,
            tasks: old.tasks.filter((t) => t.id !== variables.taskId),
          };
        });
        return { prevTasks, prevTask };
      },
      onError: (err, vars, context) => {
        if (context?.prevTasks) {
          const queryKeyTasks = getGetTasksQueryOptions().queryKey;
          qc.setQueryData(queryKeyTasks, context.prevTasks);
        }
        if (context?.prevTask) {
          const queryKeyTask = getGetTasksTaskIdQueryOptions(vars.taskId).queryKey;
          qc.setQueryData(queryKeyTask, context.prevTask);
        }
        openAlertDialog({
          title: 'タスク削除に失敗しました',
          description: err,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
      onSuccess: () => {
        toast.success('タスクを削除しました');
      },
      onSettled: () => {},
    },
  });

  // ユーザーのアクセスレベル用
  const accessMap = useMemo(() => {
    if (!tasks) return new Map<number, AccessLevel>();
    const m = new Map<number, AccessLevel>();
    if (tasks) {
      for (const t of tasks) {
        const lvl = (t as Task).user_access_level as AccessLevel | undefined;
        if (lvl) m.set(Number(t.id), lvl);
      }
    }
    return m;
  }, [tasks]);

  const levelOf: LevelResolver = useCallback(
    (taskId: number) => accessMap.get(taskId),
    [accessMap]
  );
  const can = useCallback(
    (action: Action, subject: Subject) => rawCan(action, subject, levelOf, currentUserId),
    [levelOf, currentUserId]
  );
  //{...getDisabledProps('progress.update',obj)}
  const getDisabledProps = useCallback(
    (action: Action, subject: Subject) => {
      const allowed = can(action, subject);
      return { disabled: !allowed, 'aria-disabled': !allowed };
    },
    [can]
  );

  return (
    <TaskContext.Provider
      value={{
        tasks,
        isLoading,
        createTask,
        createTaskAsync,
        updateTask,
        updateTaskOrder,
        deleteTask,
        refetch,
        levelOf,
        can,
        getDisabledProps,
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};
