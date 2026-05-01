// src/components/task/taskScopeModal/SingleUserSelectModal.tsx
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription,DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

import { useGetTasksTaskIdAuthorizedUsers } from "@/api/generated/taskProgressAPI";
import type { UserWithScopes } from "@/api/generated/taskProgressAPI.schemas";

type PickedUser = { id: number; name: string};

type Props = {
  taskId: number;
  open: boolean;
  onClose: () => void;
  onConfirm: (user: PickedUser) => void; // 単一のユーザーを返す
  /** 選択肢から除外したいユーザーID（既に選択済み等） */
  excludedUserIds?: number[];
  /** このID配下のユーザーだけに絞る（任意） */
  organizationId?: number | null;
};

export const SingleUserSelectModal = ({
  taskId,
  open,
  onClose,
  onConfirm,
  excludedUserIds = [],
}: Props) => {
  const [q, setQ] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null); // 単一選択用の状態

  // Orval 生成の hook 仕様に合わせて params / options を渡す
  const { data, isLoading, isError } = useGetTasksTaskIdAuthorizedUsers(
    taskId,
    {
      query: { enabled: open }, // モーダルが開いた時だけ fetch
    }
  );

  // 初期化（モーダルオープン毎に選択状態クリア）
  useEffect(() => {
    if (open) setSelectedUserId(null);
  }, [open]);

  const availableUsers: UserWithScopes[] = useMemo(() => {
    const list = Array.isArray(data) ? (data as UserWithScopes[]) : [];
    const filteredByOrg = list.filter(
      (u) => !excludedUserIds.includes(u.id ?? -1)
    );
    if (!q.trim()) return filteredByOrg;
    const query = q.trim().toLowerCase();
    return filteredByOrg.filter((u) => {
      const name = (u.name ?? "").toLowerCase();
      const organization = (u.organization_name ?? "").toLowerCase();
      return name.includes(query) || organization.includes(query);
    });
  }, [data, q, excludedUserIds]);

  const handleUserSelect = (id: number) => {
    setSelectedUserId(id);
  };

  const handleConfirm = () => {
    if (selectedUserId) {
      const selectedUser = availableUsers.find((u) => u.id === selectedUserId);
      if (selectedUser) {
        const picked: PickedUser = {
          id: selectedUser.id as number,
          name: selectedUser.name,
        };
        onConfirm(picked);
        onClose();
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => (!v ? onClose() : null)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>ユーザーを選択</DialogTitle>
          <DialogDescription>1人のユーザーを選択してください。</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2">
          <Input
            placeholder="検索（名前）/ 組織名"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Button variant="outline" onClick={() => setQ("")}>
            クリア
          </Button>
        </div>

        <div className="border rounded-md">
          <ScrollArea className="h-72">
            {isLoading && (
              <div className="p-4 text-sm text-muted-foreground">読み込み中...</div>
            )}
            {isError && (
              <div className="p-4 text-sm text-red-600">ユーザーの取得に失敗しました。</div>
            )}
            {!isLoading && !isError && availableUsers.length === 0 && (
              <div className="p-4 text-sm text-muted-foreground">該当するユーザーがいません。</div>
            )}
            <ul className="divide-y">
              {availableUsers.map((u) => (
                <li key={u.id} className="flex items-center gap-2 p-3">
                  <input
                    type="radio"
                    id={`u-${u.id}`}
                    name="user-select"
                    checked={selectedUserId === u.id}
                    onChange={() => u.id != null && handleUserSelect(u.id)}
                    className="w-4 h-4"
                  />
                  <label
                    htmlFor={`u-${u.id}`}
                    className="flex-1 cursor-pointer"
                    title={u.name}
                  >
                    <div className="font-medium">{u.name}</div>
                    <div className="text-xs text-muted-foreground">{u.organization_name}</div>
                  </label>
                </li>
              ))}
            </ul>
          </ScrollArea>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            キャンセル
          </Button>
          <Button onClick={handleConfirm} disabled={!selectedUserId}>
            選択する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};