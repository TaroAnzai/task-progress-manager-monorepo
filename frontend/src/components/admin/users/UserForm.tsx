// src/components/admin/user/UserForm.tsx

import React, { useEffect, useState } from 'react';

import { toast } from "sonner";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { usePostAccessScopesUsersUserId, usePostUsers, usePutUsersUserId } from '@/api/generated/taskProgressAPI';
import { UserInputRole } from '@/api/generated/taskProgressAPI.schemas';

import { useAlertDialog } from "@/context/useAlertDialog";

import { OrganizationSelectorDialog } from './OrganizationSelectorDialog';
import type { OrganizationSelectResult, UserFormState } from './types';

interface UserFormProps {
  initialData: UserFormState | null;
  companyId: number;
  onSubmitted: () => void;
  onCancel: () => void;
}

const emptyForm: UserFormState = {
  id: 0,
  name: '',
  email: '',
  //organization_code: '',
  organization_id: 0,
  role: UserInputRole.MEMBER,
};

export const UserForm: React.FC<UserFormProps> = ({ initialData, companyId, onSubmitted }) => {
  const [form, setForm] = useState<UserFormState>(emptyForm);
  const [orgDialogOpen, setOrgDialogOpen] = useState(false);
  const [orgDisplayName, setOrgDisplayName] = useState<string>('組織を選択');

  const createUserMutation = usePostUsers();
  const updateUserMutation = usePutUsersUserId();
  const addScopeMutation = usePostAccessScopesUsersUserId();
  const { openAlertDialog } = useAlertDialog();

  useEffect(() => {
    if (initialData) {
      setForm(initialData);
      setOrgDisplayName('組織を選択');
    } else {
      setForm(emptyForm);
      setOrgDisplayName('組織を選択');
    }
  }, [initialData]);

  const handleChange = (key: keyof UserFormState, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const handleOrgSelect = (org: OrganizationSelectResult) => {
    setForm(prev => ({ ...prev, organization_code: org.org_code, organization_id: org.org_id }));
    setOrgDisplayName(`${org.org_name} (${org.org_code})`);
    setOrgDialogOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.name || !form.email || !form.organization_id) {
      openAlertDialog({ title: 'エラー', description: '名前、メール、組織コードは必須です', showCancel: false });
      return;
    }

    try {
      if (form.id) {
        await updateUserMutation.mutateAsync({
          userId: form.id,
          data: {
            name: form.name,
            email: form.email,
            organization_id: form.organization_id,
          },
        });
        await addScopeMutation.mutateAsync({
          userId: form.id,
          data: {
            organization_id: form.organization_id,
            role: form.role,
            user_id: form.id,
          },
        });
      } else {
        const result = await createUserMutation.mutateAsync({
          data: {
            name: form.name,
            email: form.email,
            password: form.email, // 仮にメールアドレスをパスワードとして使用
            organization_id: form.organization_id,
          },
        });

        await addScopeMutation.mutateAsync({
          userId: result.user.id,
          data: {
            user_id: result.user.id,
            organization_id: form.organization_id,
            role: form.role,
          },
        });
      }

      onSubmitted();
      toast.success('保存しました', { description: `ユーザー${form.name}を保存しました` });
      clearForm();
    } catch (err) {
      openAlertDialog({ title: 'エラー', description: err, showCancel: false });
    }
  };

  const clearForm = () => {
    setForm(emptyForm);
    setOrgDisplayName('組織を選択');
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <Input
        placeholder="氏名"
        value={form.name}
        onChange={(e) => handleChange('name', e.target.value)}
      />
      <Input
        type="email"
        placeholder="メールアドレス"
        value={form.email}
        onChange={(e) => handleChange('email', e.target.value)}
      />

      <div className="flex items-center gap-2">
        <Button type="button" variant="outline" onClick={() => setOrgDialogOpen(true)}>
          {orgDisplayName}
        </Button>
        <Select value={form.role} onValueChange={(val) => handleChange('role', val as UserFormState['role'])}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="権限" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={UserInputRole.SYSTEM_ADMIN}>システム管理者</SelectItem>
            <SelectItem value={UserInputRole.ORG_ADMIN}>組織管理者</SelectItem>
            <SelectItem value={UserInputRole.MEMBER}>メンバー</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={clearForm}>キャンセル</Button>
        <Button type="submit">{form.id ? '更新' : '登録'}</Button>
      </div>

      <OrganizationSelectorDialog
        companyId={companyId}
        open={orgDialogOpen}
        onClose={() => setOrgDialogOpen(false)}
        onSelect={handleOrgSelect}
      />
    </form>
  );
};


