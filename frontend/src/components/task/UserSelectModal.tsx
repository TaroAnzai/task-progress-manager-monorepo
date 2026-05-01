// src/components/task/taskScopeModal/UserScopeSelectModal.tsx
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

import { useGetUsers } from "@/api/generated/taskProgressAPI";
import type { User } from "@/api/generated/taskProgressAPI.schemas";

type PickedUser = { id: number; name: string };

type Props = {
  open: boolean;
  onClose: () => void;
  onConfirm: (users: PickedUser[]) => void;
  /** 選択肢から除外したいユーザーID（既に選択済み等） */
  excludedUserIds?: number[];
  /** このID配下のユーザーだけに絞る（任意） */
  organizationId?: number | null;
};

export const UserSelectModal = ({
  open,
  onClose,
  onConfirm,
  excludedUserIds = [],
}: Props) => {
  const [q, setQ] = useState("");
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  // Orval 生成の hook 仕様に合わせて params / options を渡す
  // 例: useGetUsers(params?, options?)
  const { data, isLoading, isError } = useGetUsers({
    query: { enabled: open }, // モーダルが開いた時だけ fetch
  });

  // 初期化（モーダルオープン毎に選択状態クリア）
  useEffect(() => {
    if (open) setChecked({});
  }, [open]);

  const availableUsers: User[] = useMemo(() => {
    const list = Array.isArray(data) ? (data as User[]) : [];
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

  const toggle = (id: number, next?: boolean) => {
    setChecked((prev) => ({ ...prev, [id]: next ?? !prev[id] }));
  };

  const allVisibleChecked = useMemo(() => {
    if (availableUsers.length === 0) return false;
    return availableUsers.every((u) => !!u.id && checked[u.id]);
  }, [availableUsers, checked]);

  const onToggleAll = () => {
    const next = !allVisibleChecked;
    const updated: Record<number, boolean> = { ...checked };
    for (const u of availableUsers) {
      if (u.id != null) updated[u.id] = next;
    }
    setChecked(updated);
  };

  const handleConfirm = () => {
    const picked: PickedUser[] = availableUsers
      .filter((u) => !!u.id && checked[u.id])
      .map((u) => ({
        id: u.id as number,
        name: u.name,
      }));
    onConfirm(picked);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => (!v ? onClose() : null)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>ユーザーを選択</DialogTitle>
          <DialogDescription></DialogDescription>
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

        <div className="flex items-center gap-2">
          <Checkbox
            id="check-all"
            checked={allVisibleChecked}
            onCheckedChange={() => onToggleAll()}
          />
          <label htmlFor="check-all" className="text-sm text-muted-foreground cursor-pointer">
            表示中をすべて選択 / 解除
          </label>
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
                  <Checkbox
                    id={`u-${u.id}`}
                    checked={!!(u.id && checked[u.id])}
                    onCheckedChange={(val) => u.id != null && toggle(u.id, !!val)}
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
          <Button onClick={handleConfirm} disabled={Object.values(checked).every((v) => !v)}>

            追加する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};


