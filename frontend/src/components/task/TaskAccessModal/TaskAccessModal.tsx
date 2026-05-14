import { useEffect, useMemo, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  getGetTasksTaskIdAccessLevelsQueryKey,
  useGetTasksAccessSubjectsSearch,
  useGetTasksTaskIdAccessLevels,
  usePutTasksTaskIdAccessLevels,
} from '@/api/generated/taskProgressAPI';

import { extractErrorMessage } from '@/utils/errorHandler';

import { AccessSubjectSearchBox } from './AccessSubjectSearchBox';
import { getSubjectKey, hasAccessItem, isSameSubject } from './accessSubjectUtils';
import { CurrentAccessList } from './CurrentAccessList';
import { toAccessLevelInput, toTaskAccessItems } from './taskAccessMapper';
import type { AccessSubjectItem, EditableTaskAccessLevel, TaskAccessItem } from './taskAccessTypes';

// 実際のOrval生成フックに置き換え
// import {
//   useGetTasksTaskIdAccessLevels,
//   usePutTasksTaskIdAccessLevels,
//   useGetAccessSubjectsSearch,
// } from '@/api/generated/taskProgressAPI';

type TaskAccessModalProps = {
  open: boolean;
  taskId: number;
  taskTitle: string;
  onClose: () => void;
  onSaved?: () => void;
};

export const TaskAccessModal = ({
  open,
  taskId,
  taskTitle,
  onClose,
  onSaved,
}: TaskAccessModalProps) => {
  const qc = useQueryClient();
  const [items, setItems] = useState<TaskAccessItem[]>([]);
  const [keyword, setKeyword] = useState('');

  const accessLevelsQuery = useGetTasksTaskIdAccessLevels(taskId);
  const searchQuery = useGetTasksAccessSubjectsSearch(
    { keyword: keyword },
    {
      query: {
        enabled: !!keyword,
      },
    }
  );

  const { mutate: updateMutation, isPending: isUpdating } = usePutTasksTaskIdAccessLevels({
    mutation: {
      onSuccess: () => {
        const queryKey = getGetTasksTaskIdAccessLevelsQueryKey(taskId);
        qc.invalidateQueries({ queryKey });
        toast.success('アクセス権限を更新しました');
        onSaved?.();
        onClose();
      },
      onError: (e) => {
        const err = extractErrorMessage(e);
        toast.error('アクセス権限の更新に失敗しました', { description: err });
        console.error(err);
      },
    },
  });

  const initialItems = useMemo(
    () => toTaskAccessItems(accessLevelsQuery.data?.accesses ?? []),
    [accessLevelsQuery.data]
  );

  useEffect(() => {
    if (!open) return;

    setItems(initialItems);
  }, [open, initialItems]);

  const searchResults: AccessSubjectItem[] = useMemo(
    () =>
      searchQuery.data?.subjects.map((item) => ({
        subjectType: item.subject_type,
        refId: item.ref_id,
        name: item.display_name ?? item.display_name ?? '(名称未設定)',
        description: item.description ?? '',
      })) ?? [],
    [searchQuery.data]
  );

  const normalizedSearchResults = useMemo(
    () =>
      searchResults.map((result) => ({
        ...result,
        alreadyAdded: hasAccessItem(items, result),
      })),
    [searchResults, items]
  );

  const hasChanged = useMemo(() => {
    const before = initialItems.map((item) => ({
      key: getSubjectKey(item),
      accessLevel: item.accessLevel,
    }));

    const after = items.map((item) => ({
      key: getSubjectKey(item),
      accessLevel: item.accessLevel,
    }));

    return JSON.stringify(before) !== JSON.stringify(after);
  }, [initialItems, items]);

  if (!open) return null;

  const handleAddSubject = (subject: AccessSubjectItem) => {
    setItems((current) => {
      if (hasAccessItem(current, subject)) {
        return current;
      }

      return [
        ...current,
        {
          ...subject,
          accessLevel: 'VIEW',
        },
      ];
    });
  };

  const handleChangeAccessLevel = (
    target: TaskAccessItem,
    accessLevel: EditableTaskAccessLevel
  ) => {
    setItems((current) =>
      current.map((item) => {
        if (!isSameSubject(item, target)) return item;
        if (item.accessLevel === 'OWNER') return item;

        return {
          ...item,
          accessLevel,
        };
      })
    );
  };

  const handleRemove = (target: TaskAccessItem) => {
    if (target.accessLevel === 'OWNER') return;

    setItems((current) => current.filter((item) => !isSameSubject(item, target)));
  };

  const handleSave = () => {
    updateMutation({
      taskId,
      data: toAccessLevelInput(items),
    });
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4">
      <div className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl bg-white shadow-xl">
        <header className="border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900">タスク権限の管理</h2>
          <p className="mt-1 text-sm text-slate-500">
            「{taskTitle}」へのアクセス権限を設定します。
          </p>
        </header>

        <main className="flex-1 space-y-6 overflow-auto px-6 py-5">
          {accessLevelsQuery.isLoading ? (
            <div className="rounded-md border border-slate-200 px-4 py-6 text-center text-sm text-slate-500">
              権限情報を読み込み中...
            </div>
          ) : accessLevelsQuery.isError ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-6 text-center text-sm text-red-600">
              権限情報の取得に失敗しました。
            </div>
          ) : (
            <>
              <AccessSubjectSearchBox
                searchResults={normalizedSearchResults}
                isLoading={searchQuery.isLoading}
                onSearchChange={setKeyword}
                onAddSubject={handleAddSubject}
              />

              <CurrentAccessList
                items={items}
                onChangeAccessLevel={handleChangeAccessLevel}
                onRemove={handleRemove}
              />
            </>
          )}
        </main>

        <footer className="flex items-center justify-between border-t border-slate-200 px-6 py-4">
          <p className="text-xs text-slate-500">
            追加した対象はVIEWで登録されます。必要に応じて現在の権限一覧で変更してください。
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isUpdating}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              キャンセル
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={
                isUpdating ||
                accessLevelsQuery.isLoading ||
                accessLevelsQuery.isError ||
                !hasChanged
              }
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isUpdating ? '保存中...' : '保存'}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};
