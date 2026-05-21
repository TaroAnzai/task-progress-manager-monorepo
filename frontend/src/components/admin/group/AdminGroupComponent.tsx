import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  getGetGroupsGroupIdMembersQueryKey,
  getGetGroupsGroupIdQueryKey,
  getGetGroupsQueryKey,
  getGetUsersAdminQueryKey,
  useDeleteGroupsGroupId,
  useGetGroups,
  useGetGroupsGroupId,
  useGetGroupsGroupIdMembers,
  useGetOrganizations,
  usePatchGroupsGroupId,
  usePostGroups,
  usePutGroupsGroupIdMembers,
} from '@/api/generated/taskProgressAPI';
import type {
  GroupCreate,
  GroupMemberUser,
  GroupUpdate,
} from '@/api/generated/taskProgressAPI.schemas';

import { useUser } from '@/context/useUser';

import { GroupEditorPanel } from './GroupEditorPanel';
import {
  buildAllowedOrganizations,
  buildAllowedScopeOptions,
  normalizeGroupFormValuesByPermission,
} from './groupPermissionUtils';
import { GroupSidebar } from './GroupSidebar';
import type { GroupEditMode, GroupFormValues, GroupMemberDisplayUser } from './types';

const emptyFormValues = (): GroupFormValues => ({
  name: '',
  scope_type: 'PRIVATE',
  organization_id: null,
  member_user_ids: [],
  member_users: [],
});

const toGroupMemberDisplayUser = (user: GroupMemberUser): GroupMemberDisplayUser => ({
  ref_id: user.id,
  display_name: user.name,
  email: user.email,
  organization_id: user.organization_id,
  organization_name: user.organization_name,
});

export const AdminGroupComponent = () => {
  const queryClient = useQueryClient();

  const [keyword, setKeyword] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [mode, setMode] = useState<GroupEditMode>('none');
  const [formValues, setFormValues] = useState<GroupFormValues>(emptyFormValues);
  const { user, loading: userLoading } = useUser();
  const organizationsQuery = useGetOrganizations();

  const accessScopes = useMemo(() => user?.access_scopes ?? [], [user?.access_scopes]);

  const organizations = useMemo(() => organizationsQuery.data ?? [], [organizationsQuery.data]);

  const allowedScopeOptions = useMemo(() => buildAllowedScopeOptions(accessScopes), [accessScopes]);

  const allowedOrganizations = useMemo(
    () => buildAllowedOrganizations(accessScopes, organizations),
    [accessScopes, organizations]
  );
  const normalizeFormValuesByPermission = useCallback(
    (values: GroupFormValues): GroupFormValues =>
      normalizeGroupFormValuesByPermission(values, allowedScopeOptions, allowedOrganizations),
    [allowedScopeOptions, allowedOrganizations]
  );
  useEffect(() => {
    if (mode === 'none') {
      return;
    }

    const normalizedValues = normalizeFormValuesByPermission(formValues);

    const changed =
      normalizedValues.scope_type !== formValues.scope_type ||
      normalizedValues.organization_id !== formValues.organization_id;

    if (changed) {
      setFormValues(normalizedValues);
    }
  }, [mode, formValues, normalizeFormValuesByPermission]);
  const lastLoadedKeyRef = useRef<string>('');

  const groupsQuery = useGetGroups();

  const groupDetailQuery = useGetGroupsGroupId(selectedGroupId ?? 0, {
    query: {
      enabled: mode === 'edit' && selectedGroupId != null,
    },
  });

  const groupMembersQuery = useGetGroupsGroupIdMembers(selectedGroupId ?? 0, {
    query: {
      enabled: mode === 'edit' && selectedGroupId != null,
    },
  });

  const createGroupMutation = usePostGroups();
  const updateGroupMutation = usePatchGroupsGroupId();
  const deleteGroupMutation = useDeleteGroupsGroupId();
  const replaceMembersMutation = usePutGroupsGroupIdMembers();

  const filteredGroups = useMemo(() => {
    const groups = groupsQuery.data ?? [];
    const normalized = keyword.trim().toLowerCase();

    if (!normalized) {
      return groups;
    }

    return groups.filter((group) => group.name.toLowerCase().includes(normalized));
  }, [groupsQuery.data, keyword]);

  useEffect(() => {
    if (mode !== 'edit' || selectedGroupId == null || !groupDetailQuery.data) {
      return;
    }

    const memberIds = groupMembersQuery.data?.user_ids ?? [];
    const memberUsers = (groupMembersQuery.data?.users ?? []).map(toGroupMemberDisplayUser);
    const loadKey = `${selectedGroupId}:${memberIds.join(',')}`;

    if (lastLoadedKeyRef.current === loadKey) {
      return;
    }

    setFormValues({
      name: groupDetailQuery.data.name,
      scope_type: groupDetailQuery.data.scope_type,
      organization_id: groupDetailQuery.data.organization_id ?? null,
      member_user_ids: memberIds,
      member_users: memberUsers,
    });

    lastLoadedKeyRef.current = loadKey;
  }, [mode, selectedGroupId, groupDetailQuery.data, groupMembersQuery.data]);

  const handleCreateNew = () => {
    setSelectedGroupId(null);
    setMode('create');
    setFormValues(emptyFormValues());
    lastLoadedKeyRef.current = '';
  };

  const handleSelectGroup = (groupId: number) => {
    setSelectedGroupId(groupId);
    setMode('edit');
    lastLoadedKeyRef.current = '';
  };

  const invalidateGroupQueries = async (groupId?: number) => {
    await queryClient.invalidateQueries({
      queryKey: getGetGroupsQueryKey(),
    });

    if (groupId != null) {
      await queryClient.invalidateQueries({
        queryKey: getGetGroupsGroupIdQueryKey(groupId),
      });

      await queryClient.invalidateQueries({
        queryKey: getGetGroupsGroupIdMembersQueryKey(groupId),
      });
    }

    await queryClient.invalidateQueries({
      queryKey: getGetUsersAdminQueryKey(),
    });
  };

  const validateForm = (): string | null => {
    if (!formValues.name.trim()) {
      return 'グループ名を入力してください。';
    }

    if (formValues.scope_type === 'ORGANIZATION' && formValues.organization_id == null) {
      return '組織グループの場合は組織IDを入力してください。';
    }

    if (formValues.member_user_ids.length === 0) {
      return 'メンバーを1人以上追加してください。';
    }

    return null;
  };

  const handleSave = async () => {
    const validationError = validateForm();

    if (validationError) {
      toast.error(validationError);
      return;
    }

    if (mode === 'create') {
      const payload: GroupCreate = {
        name: formValues.name.trim(),
        scope_type: formValues.scope_type,
        organization_id:
          formValues.scope_type === 'ORGANIZATION' ? formValues.organization_id : null,
        member_user_ids: formValues.member_user_ids,
      };

      const createdGroup = await createGroupMutation.mutateAsync({
        data: payload,
      });

      await invalidateGroupQueries(createdGroup.id);

      setSelectedGroupId(createdGroup.id);
      setMode('edit');
      toast.success('グループを作成しました');
      return;
    }

    if (mode === 'edit' && selectedGroupId != null) {
      const groupPayload: GroupUpdate = {
        name: formValues.name.trim(),
        scope_type: formValues.scope_type,
        organization_id:
          formValues.scope_type === 'ORGANIZATION' ? formValues.organization_id : null,
      };

      await updateGroupMutation.mutateAsync({
        groupId: selectedGroupId,
        data: groupPayload,
      });

      await replaceMembersMutation.mutateAsync({
        groupId: selectedGroupId,
        data: {
          user_ids: formValues.member_user_ids,
        },
      });

      await invalidateGroupQueries(selectedGroupId);
      toast.success('グループを保存しました。');
    }
  };

  const handleDelete = async () => {
    if (mode !== 'edit' || selectedGroupId == null) {
      return;
    }

    const ok = window.confirm('このグループを削除しますか？');

    if (!ok) {
      return;
    }

    await deleteGroupMutation.mutateAsync({
      groupId: selectedGroupId,
    });

    setSelectedGroupId(null);
    setMode('none');
    setFormValues(emptyFormValues());
    toast.success('グループを削除しました');
    lastLoadedKeyRef.current = '';
    await queryClient.invalidateQueries({
      queryKey: getGetGroupsQueryKey(),
    });
  };

  const isSaving =
    createGroupMutation.isPending ||
    updateGroupMutation.isPending ||
    replaceMembersMutation.isPending;

  const isDeleting = deleteGroupMutation.isPending;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
      <GroupSidebar
        groups={filteredGroups}
        selectedGroupId={selectedGroupId}
        keyword={keyword}
        isLoading={groupsQuery.isLoading}
        onKeywordChange={setKeyword}
        onSelectGroup={handleSelectGroup}
        onCreateNew={handleCreateNew}
      />

      <GroupEditorPanel
        mode={mode}
        value={formValues}
        allowedScopeOptions={allowedScopeOptions}
        allowedOrganizations={allowedOrganizations}
        isLoading={
          userLoading ||
          organizationsQuery.isLoading ||
          (mode === 'edit' && (groupDetailQuery.isLoading || groupMembersQuery.isLoading))
        }
        isSaving={isSaving}
        isDeleting={isDeleting}
        onChange={setFormValues}
        onSave={handleSave}
        onDelete={handleDelete}
      />
    </div>
  );
};
