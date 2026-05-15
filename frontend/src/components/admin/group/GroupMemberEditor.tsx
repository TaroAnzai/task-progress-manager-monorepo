import { useMemo, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Popover, PopoverAnchor, PopoverContent } from '@/components/ui/popover';

import { useGetTasksAccessSubjectsSearch } from '@/api/generated/taskProgressAPI';
import type { AccessSubjectSearchItem } from '@/api/generated/taskProgressAPI.schemas';

type GroupMemberEditorProps = {
  selectedUserIds: number[];
  onChange: (userIds: number[]) => void;
};

export const GroupMemberEditor = ({ selectedUserIds, onChange }: GroupMemberEditorProps) => {
  const [keyword, setKeyword] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const closeTimerRef = useRef<number | null>(null);
  const { data: serchresult, isLoading } = useGetTasksAccessSubjectsSearch({
    keyword: keyword,
    limit: 10,
    subject_type: 'USER',
  });
  const selectedUserIdSet = useMemo(() => new Set(selectedUserIds), [selectedUserIds]);
  const serchresultUsers = useMemo(() => serchresult?.subjects ?? [], [serchresult]);
  const selectedUsers = useMemo(
    () =>
      selectedUserIds
        .map((userId) => serchresultUsers.find((user) => user.ref_id === userId))
        .filter((user): user is AccessSubjectSearchItem => user != null),
    [selectedUserIds, serchresultUsers]
  );

  const addUser = (userId: number) => {
    if (selectedUserIdSet.has(userId)) {
      return;
    }

    onChange([...selectedUserIds, userId]);
    setKeyword('');
  };
  const handleFocus = () => {
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setIsFocused(true);
  };

  const handleBlur = () => {
    closeTimerRef.current = window.setTimeout(() => {
      setIsFocused(false);
    }, 150);
  };
  const removeUser = (userId: number) => {
    onChange(selectedUserIds.filter((id) => id !== userId));
  };
  const showPopover = isFocused && keyword.trim().length > 0;
  return (
    <div className="space-y-4">
      <Popover open={showPopover}>
        <PopoverAnchor asChild>
          <Input
            value={keyword}
            placeholder="ユーザー名・メール・組織名で検索"
            onChange={(event) => setKeyword(event.target.value)}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
        </PopoverAnchor>
        <PopoverContent align="start" className="w-160" onOpenAutoFocus={(e) => e.preventDefault()}>
          {isLoading ? (
            <div className="px-3 py-4 text-sm text-slate-500">検索中...</div>
          ) : serchresultUsers.length === 0 ? (
            <div className="px-3 py-4 text-sm text-slate-500">該当する対象がありません。</div>
          ) : (
            <ul className="py-1">
              {serchresultUsers.map((item) => (
                <li key={`${item.ref_id}`}>
                  <button
                    type="button"
                    //disabled={item.alreadyAdded}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => addUser(item.ref_id)}
                    className={[
                      'flex w-full items-center gap-3 px-3 py-2 text-left text-sm',
                      // item.alreadyAdded
                      //   ? 'cursor-not-allowed bg-slate-50 text-slate-400'
                      //   : 'hover:bg-slate-50',
                    ].join(' ')}
                  >
                    <span className="text-base">👤</span>

                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{item.display_name}</span>
                      {item.description && (
                        <span className="block truncate text-xs text-slate-500">
                          {item.description}
                        </span>
                      )}
                    </span>

                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                      {item.description}
                    </span>

                    {/* {item.alreadyAdded && (
                        <span className="text-xs text-slate-400">追加済み</span>
                      )} */}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </PopoverContent>
      </Popover>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-sm font-medium">現在のメンバー</h4>
          <span className="text-xs text-muted-foreground">{selectedUsers.length}名</span>
        </div>

        {selectedUsers.length === 0 && (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            メンバーがまだ追加されていません。
          </div>
        )}

        {selectedUsers.length > 0 && (
          <div className="space-y-2">
            {selectedUsers.map((user) => (
              <div
                key={user.ref_id}
                className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{user.display_name}</div>
                  <div className="truncate text-xs text-muted-foreground">{user.description}</div>
                </div>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => removeUser(user.ref_id)}
                >
                  削除
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
