import { useState } from "react";

import { AxiosError } from "axios";
import { toast } from "sonner";

import {
  useGetOrganizations,
  usePostUsers,
} from "@/api/generated/taskProgressAPI";
import type { UserInputRole } from "@/api/generated/taskProgressAPI.schemas";

import { ROLE_LABELS } from "@/context/roleLabels";

export const useBulkUserRegistration = (company_id: number) => {
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const { data: orgs } = useGetOrganizations({ company_id: company_id });
  const createUserMutation = usePostUsers();

  const registerFromLines = async (lines: string[]) => {
    setLoading(true);

    // 組織名 → 組織コードと組織コード→組織IDの辞書
    const nameToCode: Record<string, string> = {};
    const orgCodeToOrgId: Record<string, number> = {};
    const codeSet = new Set<string>();
    orgs?.forEach((org) => {
      if (org.name && org.org_code) {
        nameToCode[org.name] = org.org_code;
        codeSet.add(org.org_code);
        orgCodeToOrgId[org.org_code] = org.id;
      }
    });

    // 日本語ラベル → enum の逆変換
    const roleMap: Record<string, UserInputRole> = {};
    const entries = Object.entries(ROLE_LABELS) as [UserInputRole, string][];
    for (const [code, label] of entries) {
      roleMap[label] = code;
    }
    const errors: string[] = [];
    const success = 0;

    for (let i = 0; i < lines.length; i++) {
      const [name, email, orgCodeOrName, roleLabel] = lines[i]
        .split(",")
        .map((s) => s.trim());

      if (!name || !email || !orgCodeOrName) {
        errors.push(`行${i + 1}: 名前とメールアドレス、組織コード（組織名）は必須です`);
        continue;
      }

      // 組織名→コードに変換（存在しない場合はそのまま）
      const orgCode = nameToCode[orgCodeOrName] || orgCodeOrName;
      // 権限ラベル→enum変換（存在しない場合はそのまま）
      const role = roleMap[roleLabel] || roleLabel;

      try {
        await createUserMutation.mutateAsync({
          data: {
            name: name,
            email: email,
            password: email, // 仮にメールアドレスをパスワードとして使用
            organization_id: orgCodeToOrgId[orgCode],
            role: role,
          },
        });
      } catch (e) {
        const err = e as AxiosError<{ message?: string }>;
        errors.push(`行${i + 1}: ${err.message}`);
        continue;
      }
    }
    if (success > 0) toast.success(`登録成功：${success} 件`);
    setLoading(false);
    setErrors(errors);
  };
  return { registerFromLines, loading, errors };
};