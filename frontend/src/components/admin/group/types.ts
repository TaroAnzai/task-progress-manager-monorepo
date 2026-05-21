import type {
  GroupResponse,
  Organization,
  UserSchemaForAdmin,
} from '@/api/generated/taskProgressAPI.schemas';

export type GroupScopeType = 'PRIVATE' | 'ORGANIZATION' | 'GLOBAL';

export type GroupEditMode = 'none' | 'create' | 'edit';
export type GroupMemberDisplayUser = {
  ref_id: number;
  display_name: string;
  email?: string | null;
  organization_id?: number | null;
  organization_name?: string | null;
};
export type GroupFormValues = {
  name: string;
  scope_type: GroupScopeType;
  organization_id: number | null;
  member_user_ids: number[];
  member_users: GroupMemberDisplayUser[];
};
export type ScopeOption = {
  value: GroupScopeType;
  label: string;
};

export type OrganizationOption = Organization;
export type GroupListItemData = GroupResponse;

export type UserOption = UserSchemaForAdmin;
