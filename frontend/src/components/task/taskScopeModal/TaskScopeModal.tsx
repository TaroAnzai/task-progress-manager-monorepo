// src/components/task/taskScopeModal/TaskScopeModal.tsx
import { useEffect, useState } from "react";

import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";

import {
  useGetTasksTaskIdAccessOrganizations,
  useGetTasksTaskIdAccessUsers,
  useGetTasksTaskIdAuthorizedUsers,
  usePutTasksTaskIdAccessLevels,
} from "@/api/generated/taskProgressAPI";
import type {
  AccessUser,
  AccessUserAccessLevel,
  OrgAccess,
  Task,
} from "@/api/generated/taskProgressAPI.schemas";

import { extractErrorMessage } from "@/utils/errorHandler";

import { SCOPE_LEVEL_OPTIONS } from "@/context/roleLabels";
import { useUser } from "@/context/useUser";

import { UserSelectModal } from "../UserSelectModal";

import { OrganizationScopeSelectModal } from "./OrganizationScopeSelectModal";
import { ScopeLevelBadge } from "./ScopeLevelBadge";


export interface TaskScopeModalProps {
  task: Task;
  open: boolean;
  onClose: () => void;
}

export const TaskScopeModal = ({ task, open, onClose }: TaskScopeModalProps) => {
  const { user: currentUser } = useUser();
  const { data: authorized_users } = useGetTasksTaskIdAuthorizedUsers(task.id);
  const { data: getUsers } = useGetTasksTaskIdAccessUsers(task.id);
  const { data: getOrgs } = useGetTasksTaskIdAccessOrganizations(task.id);
  const { mutateAsync: updateAccess, isPending: isSaving } = usePutTasksTaskIdAccessLevels();

  const [isEditable, setIsEditable] = useState(false);
  const [scopeUsers, setScopeUsers] = useState<AccessUser[]>([]);
  const [scopeOrgs, setScopeOrgs] = useState<OrgAccess[]>([]);
  const [openUserModal, setOpenUserModal] = useState(false);
  const [openOrgModal, setOpenOrgModal] = useState(false);

  const scopeLevelsWithoutOwner = SCOPE_LEVEL_OPTIONS.filter(
    (l) => l.value !== "OWNER"
  );

  useEffect(() => {
    const editable = (authorized_users ?? []).some((u) => u.id === currentUser?.id);
    setIsEditable(editable);
  }, [currentUser, task, authorized_users]);
  useEffect(() => {
    if (getUsers) setScopeUsers(getUsers);
  }, [getUsers]);

  useEffect(() => {
    if (getOrgs) setScopeOrgs(getOrgs);
  }, [getOrgs]);

  const onRemoveUser = (user_id: number | undefined) => {
    const updated = scopeUsers.filter((u) => u.user_id !== user_id);
    setScopeUsers(updated);
  };
  const onRemoveOrg = (organization_id: number | undefined) => {
    const updated = scopeOrgs.filter((o) => o.organization_id !== organization_id);
    setScopeOrgs(updated);
  };
  const handleUpdateAccess = async () => {
    const accessUserInput = scopeUsers.map((u) => ({
      user_id: u.user_id,
      access_level: u.access_level,
    }))
    const orgAccessInput = scopeOrgs.map((o) => ({
      organization_id: o.organization_id,
      access_level: o.access_level,
    }))
    try {
      await updateAccess({
        taskId: task.id,
        data: { user_access: accessUserInput, organization_access: orgAccessInput },
      });
      toast.success("更新しました");
      onClose();
    } catch (e) {
      const err = extractErrorMessage(e);
      toast.error("更新に失敗しました", { description: err });
      console.error(err);
    }
  }
  const handleUsersSelected = (users: { id: number; name: string }[]) => {
    const selected: AccessUser[] = users.map((u) => (
      {
        user_id: u.id,
        name: u.name,
        access_level: 'VIEW',
      }
    ));
    setScopeUsers([...scopeUsers, ...selected]);
    setOpenUserModal(false);
  }

  const handleOrgsSelected = (org: { org_id: number; org_name: string }) => {
    const selected: OrgAccess = {
      organization_id: org.org_id,
      name: org.org_name,
      access_level: 'VIEW',
    }
    // 重複チェック
    const exists = scopeOrgs.some(
      (o) => o.organization_id === selected.organization_id
    );
    if (!exists) {
      setScopeOrgs([...scopeOrgs, selected]);
    }
    setOpenOrgModal(false);
  }
  const updateUserLevel = (user_id: number, level: AccessUserAccessLevel) => {
    const updated = scopeUsers.map((u) => {
      if (u.user_id === user_id) {
        return { ...u, access_level: level };
      }
      return u;
    });
    setScopeUsers(updated);
  };
  const updateOrgLevel = (org_id: number, level: AccessUserAccessLevel) => {
    const updated = scopeOrgs.map((o) => {
      if (o.organization_id === org_id) {
        return { ...o, access_level: level };
      }
      return o;
    });
    setScopeOrgs(updated);
  };


  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>"タスクスコープ設定"</DialogTitle>
            <DialogDescription></DialogDescription>
          </DialogHeader>
          <div className="mt-6 space-y-4">
            <div>
              <h3 className="text-base font-semibold mb-1">ユーザースコープ</h3>
              <div className="flex flex-wrap gap-2">
                {scopeUsers.map((user) => (
                  <ScopeLevelBadge
                    key={user.user_id}
                    text={user.name}
                    value={user.access_level}
                    options={scopeLevelsWithoutOwner}
                    editable={isEditable}
                    onChange={(val) => updateUserLevel(user.user_id!, val)}
                    onRemove={() => onRemoveUser(user.user_id)}
                    color="blue"
                  />
                ))}
                {isEditable && (
                  <Button size="sm" variant="outline" onClick={() => setOpenUserModal(true)}>
                    <Plus className="w-4 h-4 mr-1" /> 追加
                  </Button>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-base font-semibold mb-1">組織スコープ</h3>
              <div className="flex flex-wrap gap-2">
                {scopeOrgs.map((org) => (
                  <ScopeLevelBadge
                    key={org.organization_id}
                    text={org.name}
                    value={org.access_level}
                    options={scopeLevelsWithoutOwner}
                    editable={isEditable}
                    onChange={(val) => updateOrgLevel(org.organization_id!, val)}
                    onRemove={() => onRemoveOrg(org.organization_id)}
                    color="blue"
                  />
                ))}
                {isEditable && (
                  <Button size="sm" variant="outline" onClick={() => setOpenOrgModal(true)}>
                    <Plus className="w-4 h-4 mr-1" /> 追加
                  </Button>
                )}
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <Button variant="outline" onClick={onClose}>
              閉じる
            </Button>

            {isEditable ? (
              <Button onClick={handleUpdateAccess} disabled={isSaving}>
                {isSaving ? "保存中..." : "保存"}
              </Button>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
      <UserSelectModal
        open={openUserModal}
        onClose={() => {
          setOpenUserModal(false);
        }}
        onConfirm={(users) => {
          handleUsersSelected(users);
        }}
        excludedUserIds={[
          ...scopeUsers.map((u) => u.user_id),
          ...(currentUser ? [currentUser.id] : []),
        ]}
      />
      <OrganizationScopeSelectModal
        open={openOrgModal}
        onClose={() => {
          setOpenOrgModal(false);
        }}
        onSelect={(org) => {
          handleOrgsSelected(org);
        }}
        selectedOrgIds={scopeOrgs.map((o) => o.organization_id)}
      />
    </>
  );
};
