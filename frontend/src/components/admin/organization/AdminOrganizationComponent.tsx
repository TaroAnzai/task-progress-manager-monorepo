import React, { useEffect } from "react";

import { Card, CardContent } from '@/components/ui/card';

import { useAlertDialog } from "@/context/useAlertDialog";

import { BulkTextInputForm } from "../import/BulkTextInputForm";
import { useBulkOrganizationRegister } from "../import/useBulkOrganizationRegister";

import { OrganizationTreeView } from "./OrganizationTreeView";

/**
 * 外部からは <TreeView companyId={...} /> で使用する
 */
interface TreeViewProps {
  companyName: string;
  companyId: number;
}

export const AdminOrganizationComponent: React.FC<TreeViewProps> = ({ companyName, companyId }) => {
  const { registerFromLines: orgRegister, loading, errors } = useBulkOrganizationRegister(companyId)
  const { openAlertDialog } = useAlertDialog();

  useEffect(() => {
    if (errors.length > 0) {
      openAlertDialog({
        title: "エラー",
        description: errors.join("\n"),
        confirmText: "閉じる",
        showCancel: false,
      });
    }
  }, [errors, openAlertDialog])

  return (
    <div className="flex gap-4">
      <Card className="w-1/2">
        <CardContent>
          <OrganizationTreeView
            companyName={companyName}
            companyId={companyId}
          />
        </CardContent>
      </Card>
      <Card className="w-1/2">
        <BulkTextInputForm
          title="組織の一括登録"
          placeholder="
      組織名, 組織コード, 親組織コード
      商品部, dev01, root"
          onSubmit={orgRegister}
          loading={loading}
        />
      </Card>
    </div>

  );
};
