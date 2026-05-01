
import { AccessUserAccessLevel,UserInputRole } from '@/api/generated/taskProgressAPI.schemas.ts';


export const ROLE_LABELS: Record<UserInputRole, string> = {
  [UserInputRole.SYSTEM_ADMIN]: 'システム管理者',
  [UserInputRole.ORG_ADMIN]: '組織管理者',
  [UserInputRole.MEMBER]: 'メンバー',
};

export const SCOPE_LABELS: Record<AccessUserAccessLevel, string> = {
  [AccessUserAccessLevel.VIEW]: '閲覧権限',
  [AccessUserAccessLevel.EDIT]: '編集権限',
  [AccessUserAccessLevel.FULL]: 'フル権限',
  [AccessUserAccessLevel.OWNER]: '作成者',
};

// セレクター用配列（DropdownMenuなどで利用）
export const SCOPE_LEVEL_OPTIONS = Object.values(AccessUserAccessLevel).map(
  (value) => ({
    value,            // AccessUserAccessLevel型
    label: SCOPE_LABELS[value],
  })
);