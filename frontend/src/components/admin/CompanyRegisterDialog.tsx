import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import {
  useGetCompanies,
  usePostCompanies,
  usePostOrganizations,
  usePostUsers,
} from "@/api/generated/taskProgressAPI";
import { UserInputRole } from "@/api/generated/taskProgressAPI.schemas";

import { extractErrorMessage } from "@/utils/errorHandler";

import { useAlertDialog } from "@/context/useAlertDialog";

interface CompanyRegisterDialogProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
}

export const CompanyRegisterDialog = ({ open, onClose }: CompanyRegisterDialogProps) => {
  const [name, setName] = useState("");
  const [rootOrgName, setRootOrgName] = useState("");
  const [systemAdminName, setSystemAdminName] = useState("");
  const [systemAdminEmail, setSystemAdminEmail] = useState("");
  const { refetch } = useGetCompanies();
  const { openAlertDialog } = useAlertDialog();

  const createCompanyMutation = usePostCompanies();
  const createRootOrgMutation = usePostOrganizations();
  const createUserMutation = usePostUsers();

  const handleSubmit = async () => {
    if (!name.trim()) return;
    const registerCompanyName = name.trim();
    const registeRootOrgName = rootOrgName.trim();
    const registerSystemAdminName = systemAdminName.trim();
    const registerSystemAdminEmail = systemAdminEmail.trim();
    if (
      !registerCompanyName ||
      !registeRootOrgName ||
      !registerSystemAdminName ||
      !registerSystemAdminEmail
    ) {
      openAlertDialog({
        title: "登録エラー",
        description:
          "会社名、ルート組織名、システム管理者名、システム管理者メールアドレスを入力してください。",
        showCancel: false,
      });
      return;
    }
    try {
      const createCompany = await createCompanyMutation.mutateAsync({
        data: { name: registerCompanyName },
      });
      const createOrgData = {
        name: registeRootOrgName,
        org_code: "ROOT",
        company_id: createCompany.id,
      };
      const createRootOrg = await createRootOrgMutation.mutateAsync({
        data: createOrgData,
      });
      const createUserData = {
        name: registerSystemAdminName,
        email: registerSystemAdminEmail,
        password: registerSystemAdminEmail,
        role: UserInputRole.SYSTEM_ADMIN,
        organization_id: createRootOrg.id,
      };
      await createUserMutation.mutateAsync({ data: createUserData });
      onClose();
      refetch();
    } catch (error) {
      const errorMessage = extractErrorMessage(error);
      openAlertDialog({
        title: "登録エラー",
        description: errorMessage || "会社の登録に失敗しました。",
        showCancel: false,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>会社を登録</DialogTitle>
          <DialogDescription>新しい会社を登録してください。</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <Input
            type="text"
            placeholder="会社名を入力"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <p className="text-sm text-gray-500"> ルート組織名を入力してください。</p>
          <Input
            type="text"
            placeholder="ルート組織名を入力"
            value={rootOrgName}
            onChange={(e) => setRootOrgName(e.target.value)}
          />
          <p className="text-sm text-gray-500">組織の管理者を入力してください。</p>
          <Input
            type="text"
            placeholder="組織の管理者名を入力"
            value={systemAdminName}
            onChange={(e) => setSystemAdminName(e.target.value)}
          />
          <Input
            type="email"
            placeholder="組織の管理者メールアドレスを入力"
            value={systemAdminEmail}
            onChange={(e) => setSystemAdminEmail(e.target.value)}
          />
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={handleSubmit}>登録</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
