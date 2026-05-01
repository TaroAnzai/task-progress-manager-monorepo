// src/admin/components/user/AdminUserComponent.tsx

import React, { useCallback, useEffect, useState } from 'react';

import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

import { useGetUsersAdmin } from '@/api/generated/taskProgressAPI';
import type { UserSchemaForAdmin } from '@/api/generated/taskProgressAPI.schemas';
import { AccessScopeRole } from '@/api/generated/taskProgressAPI.schemas';

import { useAlertDialog } from '@/context/useAlertDialog';
import { useUser } from '@/context/useUser.ts';

import { BulkTextInputForm } from '../import/BulkTextInputForm.tsx';
import { useBulkUserRegistration } from '../import/useBulkUserRegister.ts';

import type { UserFormState } from './types.ts';
import { UserForm } from './UserForm.tsx';
import { UserTable } from './UserTable.tsx';

interface AdminUserComponentProps {
  companyId: number;
}

export const AdminUserComponent: React.FC<AdminUserComponentProps> = ({ companyId }) => {
  const { hasAdminScope } = useUser();
  const [editingUser, setEditingUser] = useState<UserFormState | null>(null);
  const { registerFromLines: userRegister, loading, errors } = useBulkUserRegistration(companyId);
  const { openAlertDialog } = useAlertDialog();

  useEffect(() => {
    if (errors.length > 0) {
      openAlertDialog({
        title: 'エラー',
        description: errors.join('\n'),
        confirmText: '閉じる',
        showCancel: false,
      });
    }
  }, [errors, openAlertDialog]);
  const {
    data: users,
    isLoading,
    error,
    refetch,
  } = useGetUsersAdmin({ company_id: companyId });

  const handleEditUser = useCallback((user: UserSchemaForAdmin) => {
    const matchedScope = user.access_scopes?.find(
      (s) => s.organization_id === user.organization_id
    );
    setEditingUser({
      id: user.id,
      name: user.name,
      email: user.email ?? '',
      //organization_code: user.organization_code,
      organization_id: user.organization_id,
      role: matchedScope?.role ?? AccessScopeRole.MEMBER,
    });
  }, []);

  const handleFormSubmitted = useCallback(() => {
    setEditingUser(null);
    refetch(); // 一覧更新
  }, [refetch]);

  if (!hasAdminScope()) {
    return (
      <div className="p-4 text-red-600 font-semibold">
        このユーザーにはユーザー管理の権限がありません
      </div>
    );
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">👤 ユーザー登録・編集</h2>
      <div className="p-4 space-y-4 flex gap-4">
        <Card className="w-1/2">
          <CardContent className="p-4">
            <UserForm
              initialData={editingUser}
              companyId={companyId}
              onSubmitted={handleFormSubmitted}
              onCancel={() => setEditingUser(null)}
            />
          </CardContent>
        </Card>
        <Card className="w-1/2">
          <BulkTextInputForm
            title="ユーザーの一括登録"
            placeholder="
            名前, メールアドレス, 組織コード,権限
            山田太郎, taro@foo.com, root, member"
            onSubmit={userRegister}
            loading={loading}
          />
        </Card>
      </div>
      <Separator />
      <div>
        <Card>
          <CardContent className="p-4">
            <h2 className="text-xl font-bold mb-4">📋 ユーザー一覧</h2>
            <UserTable
              users={users ?? []}
              isLoading={isLoading}
              error={error}
              onEditUser={handleEditUser}
              onRefresh={refetch}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
