import {
  type AccessScope,
  AccessScopeRole,
  type Organization,
} from '@/api/generated/taskProgressAPI.schemas';

import type { GroupFormValues, GroupScopeType, OrganizationOption, ScopeOption } from './types';

const groupScopeLabels: Record<GroupScopeType, string> = {
  PRIVATE: '個人グループ',
  ORGANIZATION: '組織グループ',
  GLOBAL: '全体グループ',
};

export const buildAllowedScopeOptions = (scopes: readonly AccessScope[]): ScopeOption[] => {
  const hasSystemAdmin = scopes.some((scope) => scope.role === AccessScopeRole.SYSTEM_ADMIN);

  if (hasSystemAdmin) {
    return [
      { value: 'PRIVATE', label: groupScopeLabels.PRIVATE },
      { value: 'ORGANIZATION', label: groupScopeLabels.ORGANIZATION },
      { value: 'GLOBAL', label: groupScopeLabels.GLOBAL },
    ];
  }

  const hasOrgAdmin = scopes.some((scope) => scope.role === AccessScopeRole.ORG_ADMIN);

  if (hasOrgAdmin) {
    return [
      { value: 'PRIVATE', label: groupScopeLabels.PRIVATE },
      { value: 'ORGANIZATION', label: groupScopeLabels.ORGANIZATION },
    ];
  }

  return [{ value: 'PRIVATE', label: groupScopeLabels.PRIVATE }];
};

export const buildAllowedOrganizations = (
  scopes: readonly AccessScope[],
  allOrganizations: readonly Organization[]
): OrganizationOption[] => {
  const hasSystemAdmin = scopes.some((scope) => scope.role === AccessScopeRole.SYSTEM_ADMIN);

  if (hasSystemAdmin) {
    return [...allOrganizations];
  }

  const orgAdminOrganizationIds = new Set(
    scopes
      .filter((scope) => scope.role === AccessScopeRole.ORG_ADMIN)
      .map((scope) => scope.organization_id)
      .filter((organizationId): organizationId is number => organizationId != null)
  );

  return allOrganizations.filter((organization) => orgAdminOrganizationIds.has(organization.id));
};

export const normalizeGroupFormValuesByPermission = (
  values: GroupFormValues,
  allowedScopeOptions: readonly ScopeOption[],
  allowedOrganizations: readonly OrganizationOption[]
): GroupFormValues => {
  const allowedScopeValues = new Set(allowedScopeOptions.map((option) => option.value));

  if (!allowedScopeValues.has(values.scope_type)) {
    return {
      ...values,
      scope_type: 'PRIVATE',
      organization_id: null,
    };
  }

  if (values.scope_type !== 'ORGANIZATION') {
    return {
      ...values,
      organization_id: null,
    };
  }

  const allowedOrganizationIds = new Set(
    allowedOrganizations.map((organization) => organization.id)
  );

  if (values.organization_id == null || !allowedOrganizationIds.has(values.organization_id)) {
    return {
      ...values,
      organization_id: allowedOrganizations[0]?.id ?? null,
    };
  }

  return values;
};
