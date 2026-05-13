import { useMemo, useState } from 'react';

import { AccessSubjectSearchBox } from './AccessSubjectSearchBox';
import { getSubjectKey, hasAccessItem, isSameSubject } from './accessSubjectUtils';
import { CurrentAccessList } from './CurrentAccessList';
import type {
  AccessSubjectItem,
  AccessSubjectSearchResult,
  EditableTaskAccessLevel,
  TaskAccessItem,
} from './taskAccessTypes';

type TaskAccessModalProps = {
  open: boolean;
  taskTitle: string;
  initialItems: TaskAccessItem[];
  searchResults: AccessSubjectItem[];
  isSearching?: boolean;
  isSaving?: boolean;
  onSearchChange: (keyword: string) => void;
  onClose: () => void;
  onSave: (items: TaskAccessItem[]) => Promise<void> | void;
};

export const TaskAccessModal = ({
  open,
  taskTitle,
  initialItems,
  searchResults,
  isSearching = false,
  isSaving = false,
  onSearchChange,
  onClose,
  onSave,
}: TaskAccessModalProps) => {
  const [items, setItems] = useState<TaskAccessItem[]>(initialItems);

  const normalizedSearchResults: AccessSubjectSearchResult[] = useMemo(
    () =>
      searchResults.map((result) => ({
        ...result,
        alreadyAdded: hasAccessItem(items, result),
      })),
    [searchResults, items]
  );

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

        if (item.accessLevel === 'OWNER') {
          return item;
        }

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

  const handleSave = async () => {
    await onSave(items);
  };

  const hasChanged =
    JSON.stringify(
      initialItems.map((item) => ({
        key: getSubjectKey(item),
        accessLevel: item.accessLevel,
      }))
    ) !==
    JSON.stringify(
      items.map((item) => ({
        key: getSubjectKey(item),
        accessLevel: item.accessLevel,
      }))
    );

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
          <AccessSubjectSearchBox
            searchResults={normalizedSearchResults}
            isLoading={isSearching}
            onSearchChange={onSearchChange}
            onAddSubject={handleAddSubject}
          />

          <CurrentAccessList
            items={items}
            onChangeAccessLevel={handleChangeAccessLevel}
            onRemove={handleRemove}
          />
        </main>

        <footer className="flex items-center justify-between border-t border-slate-200 px-6 py-4">
          <p className="text-xs text-slate-500">
            追加した対象はVIEWで登録されます。必要に応じて現在の権限一覧で変更してください。
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              キャンセル
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving || !hasChanged}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving ? '保存中...' : '保存'}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};
