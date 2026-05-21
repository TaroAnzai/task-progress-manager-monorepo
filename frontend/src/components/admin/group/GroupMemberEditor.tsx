import { useEffect, useMemo, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Popover, PopoverAnchor, PopoverContent } from '@/components/ui/popover';

import { useGetTasksAccessSubjectsSearch } from '@/api/generated/taskProgressAPI';
import type { AccessSubjectSearchItem } from '@/api/generated/taskProgressAPI.schemas';

import type { GroupMemberDisplayUser } from './types';

type GroupMemberEditorProps = {
  initialUserIds: number[];
  initialUsers: GroupMemberDisplayUser[];
  onChange: (userIds: number[], users: GroupMemberDisplayUser[]) => void;
};

const toDisplayUser = (user: AccessSubjectSearchItem): GroupMemberDisplayUser => ({
  ref_id: user.ref_id,
  display_name: user.display_name,
  email: user.email,
  organization_name: user.organization_name,
});

export const GroupMemberEditor = ({
  initialUserIds,
  initialUsers,
  onChange,
}: GroupMemberEditorProps) => {
  const [keyword, setKeyword] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>(initialUserIds);
  const [selectedUsers, setSelectedUsers] = useState<GroupMemberDisplayUser[]>(initialUsers);
  const closeTimerRef = useRef<number | null>(null);

  useEffect(() => {
    setSelectedUserIds(initialUserIds);
    setSelectedUsers(initialUsers);
  }, [initialUserIds, initialUsers]);

  const { data: searchResult, isLoading } = useGetTasksAccessSubjectsSearch(
    {
      keyword: keyword,
      limit: 10,
      subject_type: 'USER',
    },
    {
      query: {
        enabled: keyword.trim().length > 0,
      },
    }
  );

  const selectedUserIdSet = useMemo(() => new Set(selectedUserIds), [selectedUserIds]);
  const searchResultUsers = useMemo(() => searchResult?.subjects ?? [], [searchResult]);

  const addUser = (user: AccessSubjectSearchItem) => {
    if (selectedUserIdSet.has(user.ref_id)) {
      return;
    }

    const nextUserIds = [...selectedUserIds, user.ref_id];
    const nextUsers = [...selectedUsers, toDisplayUser(user)];

    setSelectedUserIds(nextUserIds);
    setSelectedUsers(nextUsers);
    onChange(nextUserIds, nextUsers);
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
    const nextUserIds = selectedUserIds.filter((id) => id !== userId);
    const nextUsers = selectedUsers.filter((user) => user.ref_id !== userId);

    setSelectedUserIds(nextUserIds);
    setSelectedUsers(nextUsers);
    onChange(nextUserIds, nextUsers);
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
          ) : searchResultUsers.length === 0 ? (
            <div className="px-3 py-4 text-sm text-slate-500">該当する対象がありません。</div>
          ) : (
            <ul className="py-1">
              {searchResultUsers.map((item) => {
                const alreadySelected = selectedUserIdSet.has(item.ref_id);

                return (
                  <li key={`${item.ref_id}`}>
                    <button
                      type="button"
                      disabled={alreadySelected}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => addUser(item)}
                      className={[
                        'flex w-full items-center gap-3 px-3 py-2 text-left text-sm',
                        alreadySelected
                          ? 'cursor-not-allowed bg-slate-50 text-slate-400'
                          : 'hover:bg-slate-50',
                      ].join(' ')}
                    >
                      <span className="text-base">👤</span>

                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{item.display_name}</span>
                        {item.email && (
                          <span className="block truncate text-xs text-slate-500">
                            {item.email}
                          </span>
                        )}
                      </span>

                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                        {item.organization_name}
                      </span>

                      {alreadySelected && <span className="text-xs text-slate-400">追加済み</span>}
                    </button>
                  </li>
                );
              })}
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
                  <div className="truncate text-xs text-muted-foreground">{user.email}</div>
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
