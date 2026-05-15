import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { GroupMemberEditor } from './GroupMemberEditor';
import type { GroupEditMode, GroupFormValues, OrganizationOption, ScopeOption } from './types';

type GroupEditorPanelProps = {
  mode: GroupEditMode;
  value: GroupFormValues;
  allowedScopeOptions: ScopeOption[];
  allowedOrganizations: OrganizationOption[];
  isLoading: boolean;
  isSaving: boolean;
  isDeleting: boolean;
  onChange: (value: GroupFormValues) => void;
  onSave: () => void;
  onDelete: () => void;
};

export const GroupEditorPanel = ({
  mode,
  value,
  allowedScopeOptions,
  allowedOrganizations,
  isLoading,
  isSaving,
  isDeleting,
  onChange,
  onSave,
  onDelete,
}: GroupEditorPanelProps) => {
  if (mode === 'none') {
    return (
      <section className="rounded-xl border bg-background p-6">
        <h2 className="text-lg font-semibold">グループを選択してください</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          左側の一覧からグループを選択するか、「新規」ボタンから作成を開始できます。
        </p>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="rounded-xl border bg-background p-6">
        <p className="text-sm text-muted-foreground">読み込み中...</p>
      </section>
    );
  }

  const setValue = <K extends keyof GroupFormValues>(key: K, nextValue: GroupFormValues[K]) => {
    onChange({
      ...value,
      [key]: nextValue,
    });
  };

  return (
    <section className="rounded-xl border bg-background p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">
          {mode === 'create' ? '新規グループ作成' : 'グループ編集'}
        </h2>
        <p className="text-sm text-muted-foreground">グループ情報とメンバーを編集します。</p>
      </div>

      <div className="space-y-6">
        <div className="rounded-lg border p-4">
          <h3 className="mb-4 font-medium">基本情報</h3>

          <div className="space-y-4">
            <div>
              <Label htmlFor="group-name">グループ名</Label>
              <Input
                id="group-name"
                value={value.name}
                placeholder="例: 営業部共有グループ"
                onChange={(event) => setValue('name', event.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="scope-type">公開範囲</Label>
              <select
                id="scope-type"
                className="mt-1 h-10 w-full rounded-md border bg-background px-3 text-sm"
                value={value.scope_type}
                onChange={(event) => {
                  const scopeType = event.target.value as GroupFormValues['scope_type'];

                  onChange({
                    ...value,
                    scope_type: scopeType,
                    organization_id:
                      scopeType === 'ORGANIZATION'
                        ? (value.organization_id ?? allowedOrganizations[0]?.id ?? null)
                        : null,
                  });
                }}
              >
                {allowedScopeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {value.scope_type === 'ORGANIZATION' && (
              <div>
                <Label htmlFor="organization-id">組織</Label>

                <select
                  id="organization-id"
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={value.organization_id ?? ''}
                  onChange={(event) => {
                    const rawValue = event.target.value;

                    setValue('organization_id', rawValue === '' ? null : Number(rawValue));
                  }}
                >
                  {allowedOrganizations.length === 0 && (
                    <option value="">選択可能な組織がありません</option>
                  )}

                  {allowedOrganizations.map((organization) => (
                    <option key={organization.id} value={organization.id}>
                      {organization.name}
                    </option>
                  ))}
                </select>

                {allowedOrganizations.length === 0 && (
                  <p className="mt-1 text-xs text-destructive">
                    組織グループを作成できる組織がありません。
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="mb-4 font-medium">メンバー</h3>

          <GroupMemberEditor
            selectedUserIds={value.member_user_ids}
            onChange={(nextUserIds) => setValue('member_user_ids', nextUserIds)}
          />
        </div>

        <div className="flex justify-between gap-2">
          <div>
            {mode === 'edit' && (
              <Button
                type="button"
                variant="destructive"
                disabled={isSaving || isDeleting}
                onClick={onDelete}
              >
                {isDeleting ? '削除中...' : '削除'}
              </Button>
            )}
          </div>

          <Button type="button" disabled={isSaving || isDeleting} onClick={onSave}>
            {isSaving ? '保存中...' : '保存'}
          </Button>
        </div>
      </div>
    </section>
  );
};
