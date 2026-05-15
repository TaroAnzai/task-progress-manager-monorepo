import type {
  GroupResponse,
  Organization,
  UserSchemaForAdmin,
} from '@/api/generated/taskProgressAPI.schemas';

export type GroupScopeType = 'PRIVATE' | 'ORGANIZATION' | 'GLOBAL';

export type GroupEditMode = 'none' | 'create' | 'edit';

export type GroupFormValues = {
  name: string;
  scope_type: GroupScopeType;
  organization_id: number | null;
  member_user_ids: number[];
};
export type ScopeOption = {
  value: GroupScopeType;
  label: string;
};

export type OrganizationOption = Organization;
export type GroupListItemData = GroupResponse;

export type UserOption = UserSchemaForAdmin;
