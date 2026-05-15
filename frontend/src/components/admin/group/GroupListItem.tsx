import { cn } from '@/lib/utils';

import type { GroupListItemData } from './types';

type GroupListItemProps = {
  group: GroupListItemData;
  selected: boolean;
  onClick: () => void;
};

const scopeLabels: Record<string, string> = {
  PRIVATE: '個人',
  ORGANIZATION: '組織',
  GLOBAL: '全体',
};

export const GroupListItem = ({ group, selected, onClick }: GroupListItemProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      'w-full rounded-lg border p-3 text-left transition hover:bg-muted',
      selected && 'border-primary bg-muted'
    )}
  >
    <div className="font-medium">{group.name}</div>

    <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
      <span>{scopeLabels[group.scope_type] ?? group.scope_type}</span>

      {group.organization_id != null && <span>組織ID: {group.organization_id}</span>}

      <span>作成者ID: {group.owner_user_id}</span>
    </div>
  </button>
);
