import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import { GroupListItem } from './GroupListItem';
import type { GroupListItemData } from './types';

type GroupSidebarProps = {
  groups: GroupListItemData[];
  selectedGroupId: number | null;
  keyword: string;
  isLoading: boolean;
  onKeywordChange: (value: string) => void;
  onSelectGroup: (groupId: number) => void;
  onCreateNew: () => void;
};

export const GroupSidebar = ({
  groups,
  selectedGroupId,
  keyword,
  isLoading,
  onKeywordChange,
  onSelectGroup,
  onCreateNew,
}: GroupSidebarProps) => (
  <aside className="rounded-xl border bg-background p-4">
    <div className="mb-4 flex items-center justify-between gap-2">
      <div>
        <h2 className="text-lg font-semibold">グループ管理</h2>
        <p className="text-sm text-muted-foreground">グループを選択して編集します。</p>
      </div>

      <Button size="sm" onClick={onCreateNew}>
        新規
      </Button>
    </div>

    <div className="mb-4">
      <Input
        value={keyword}
        placeholder="グループ検索"
        onChange={(event) => onKeywordChange(event.target.value)}
      />
    </div>

    <div className="space-y-2">
      {isLoading && <p className="text-sm text-muted-foreground">読み込み中...</p>}

      {!isLoading && groups.length === 0 && (
        <p className="text-sm text-muted-foreground">グループがありません。</p>
      )}

      {groups.map((group) => (
        <GroupListItem
          key={group.id}
          group={group}
          selected={selectedGroupId === group.id}
          onClick={() => onSelectGroup(group.id)}
        />
      ))}
    </div>
  </aside>
);
