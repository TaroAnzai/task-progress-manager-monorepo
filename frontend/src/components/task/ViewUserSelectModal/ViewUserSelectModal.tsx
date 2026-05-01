//src/components/task/ViewUserSelectModal/ViewUserSelectModal.tsx

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';

export type PickedUser = { id: number; name: string };

type Props = {
  open: boolean;
  onClose: () => void;
  onSelectUser: (user: PickedUser | null) => void;
};

export const ViewUserSelectModal = ({ open, onClose, onSelectUser }: Props) => {
  const [q, setQ] = useState('');
  const { tasks } = useTasks();
  const { user } = useUser();
  const [selectedUser, setSelectedUser] = useState<PickedUser | null>(null);

  const availableUsers: PickedUser[] = useMemo(() => {
    const creaters = Array.from(
      new Map(
        (tasks ?? [])
          .filter((task): task is typeof task & { created_by: number } => task.created_by != null) // 型ガード
          .map((task) => [
            task.created_by,
            { id: task.created_by, name: task.create_user_name ?? '' },
          ])
      ).values()
    );
    const withoutCurrent = creaters.filter((c) => c.id !== user?.id);
    const available = [{ id: user?.id ?? -1, name: '自分' }, ...withoutCurrent];
    return available.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  }, [tasks, q, user]);

  const handleConfirm = () => {
    if (selectedUser) {
      if (selectedUser.id === user?.id) {
        onSelectUser(null);
      } else {
        onSelectUser(selectedUser);
      }
    }
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => (!v ? onClose() : null)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>ユーザーを選択</DialogTitle>
          <DialogDescription>表示するユーザーを選択してください。</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2">
          <Input
            placeholder="検索（名前）/ 組織名"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Button variant="outline" onClick={() => setQ('')}>
            クリア
          </Button>
        </div>

        <div className="border rounded-md">
          <ScrollArea className="h-72">
            <ul className="divide-y">
              {availableUsers.map((u) => (
                <li key={u.id} className="flex items-center gap-2 p-3">
                  <input
                    type="radio"
                    id={`u-${u.id}`}
                    name="user-select"
                    checked={selectedUser === u}
                    onChange={() => setSelectedUser(u)}
                    className="w-4 h-4"
                  />
                  <label htmlFor={`u-${u.id}`} className="flex-1 cursor-pointer" title={u.name}>
                    <div className="font-medium">{u.name}</div>
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
          <Button onClick={handleConfirm} disabled={!selectedUser}>
            選択する
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
