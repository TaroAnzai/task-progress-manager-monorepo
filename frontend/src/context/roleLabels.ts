import { AccessEntryAccessLevel, UserInputRole } from '@/api/generated/taskProgressAPI.schemas.ts';
export const getRoleLabelJa = (role?: string | null): string => {
  switch (role) {
    case 'Superuser':
      return 'スーパーユーザー';
    case 'system-admin':
      return 'システム管理者';
    case 'organization-admin':
      return '組織管理者';
    default:
      return 'メンバー';
  }
};
export const ROLE_LABELS: Record<UserInputRole, string> = {
  [UserInputRole.SYSTEM_ADMIN]: 'システム管理者',
  [UserInputRole.ORG_ADMIN]: '組織管理者',
  [UserInputRole.MEMBER]: 'メンバー',
};

export const SCOPE_LABELS: Record<AccessEntryAccessLevel, string> = {
  [AccessEntryAccessLevel.VIEW]: '閲覧権限',
  [AccessEntryAccessLevel.EDIT]: '編集権限',
  [AccessEntryAccessLevel.FULL]: 'フル権限',
  [AccessEntryAccessLevel.OWNER]: '作成者',
};

// セレクター用配列（DropdownMenuなどで利用）
export const SCOPE_LEVEL_OPTIONS = Object.values(AccessEntryAccessLevel).map((value) => ({
  value, // AccessEntryAccessLevel
  label: SCOPE_LABELS[value],
}));
