// src/components/task/TaskControlPanel.tsx
import { useState } from 'react';

import { FileDown, FilePlus, Menu, Minus, PencilIcon, Plus } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';

import { useGetExportsExcel } from '@/api/generated/taskProgressAPI';

import { NewTaskModal } from '@/components/task/newTaskModal/NewTaskModal';
import { TaskOrderSettingModal } from '@/components/task/taskSettingOrderModal/TaskOrderSettingModal';

import type { FilterAccessLevel } from '@/pages/TaskPage';

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '../ui/sheet';

import { ViewSelectorPopup } from './ViewSelectorPopup';
import { type PickedUser, ViewUserSelectModal } from './ViewUserSelectModal/ViewUserSelectModal';
interface TaskControlPanelProps {
  onAllExpand: () => void;
  onAllCollapse: () => void;
  viewMode: Record<FilterAccessLevel, boolean>;
  onChangeViewMode: (newValue: Record<FilterAccessLevel, boolean>) => void;
  onSelectUser: (user: PickedUser | null) => void;
}

export const TaskControlPanel = ({
  onAllExpand,
  onAllCollapse,
  viewMode,
  onChangeViewMode,
  onSelectUser,
}: TaskControlPanelProps) => {
  const [newTaskModalOpen, setNewTaskModalOpen] = useState(false);
  const [taskOrderModalOpen, setTaskOrderModalOpen] = useState(false);
  const [viewUserSelectModalOpen, setViewUserSelectModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<PickedUser | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  // ① 自動実行は無効化（ボタン押下で refetch）
  const { refetch: downloadFile, isFetching } = useGetExportsExcel({
    query: { enabled: false, refetchOnWindowFocus: false },
  });

  const handleDownload = async () => {
    try {
      const res = await downloadFile();
      if (!res.data || res.data instanceof Blob === false) {
        toast.error('ファイルが取得できませんでした');
        return;
      }
      const blob = res.data;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'tasks.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    }
  };
  const handleSelectUser = (user: PickedUser | null) => {
    setSelectedUser(user);
    onSelectUser(user);
  };
  const ControlButtons = (
    <>
      <Button
        onClick={() => {
          setNewTaskModalOpen(true);
        }}
        className="flex items-center gap-1"
        disabled={selectedUser !== null}
      >
        <FilePlus size={16} />
        タスク新規作成
      </Button>

      <Button
        onClick={() => {
          setTaskOrderModalOpen(true);
        }}
        variant="outline"
        className="flex items-center gap-1"
        disabled={selectedUser !== null}
      >
        <PencilIcon size={16} />
        表示順変更・削除
      </Button>

      <Button
        onClick={() => {
          handleDownload();
        }}
        variant="secondary"
        id="view-selecter-btn"
        className="flex items-center gap-1"
        disabled={selectedUser !== null}
      >
        {isFetching ? (
          <>'Excel出力中...'</>
        ) : (
          <>
            <FileDown size={16} />
            ダウンロード
          </>
        )}
      </Button>
    </>
  );
  const ViewButtons = (
    <>
      <Button onClick={() => setViewUserSelectModalOpen(true)}>
        {selectedUser ? selectedUser.name : '表示ユーザー選択'}
      </Button>
      <ViewSelectorPopup viewMode={viewMode} onChange={onChangeViewMode} />
      <Button className="" onClick={onAllExpand}>
        <Plus />
      </Button>
      <Button className="" onClick={onAllCollapse}>
        <Minus />
      </Button>
    </>
  );
  return (
    <>
      {/* --- PC版 --- */}
      <div className="hidden md:flex justify-between gap-2 mb-4" id="task-controls-box">
        <div className="flex gap-2 ">{ControlButtons}</div>
        <div className="flex gap-2">{ViewButtons}</div>
      </div>

      {/* --- スマホ版 --- */}
      <div className="flex md:hidden justify-between items-center mb-4">
        <Button onClick={() => setViewUserSelectModalOpen(true)} size="sm" variant="outline">
          {selectedUser ? selectedUser.name : '表示ユーザー選択'}
        </Button>

        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <SheetTrigger asChild>
            <Button size="icon" variant="ghost">
              <Menu />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-64">
            <SheetHeader>
              <SheetTitle>操作メニュー</SheetTitle>
            </SheetHeader>
            <div className="flex flex-col gap-2 mt-4">
              {ControlButtons}
              <div className="border-t my-2" />
              {ViewButtons}
            </div>
          </SheetContent>
        </Sheet>
      </div>
      {newTaskModalOpen && (
        <NewTaskModal open={newTaskModalOpen} onClose={() => setNewTaskModalOpen(false)} />
      )}
      {taskOrderModalOpen && (
        <TaskOrderSettingModal
          open={taskOrderModalOpen}
          onClose={() => {
            setTaskOrderModalOpen(false);
          }}
        />
      )}
      {viewUserSelectModalOpen && (
        <ViewUserSelectModal
          open={viewUserSelectModalOpen}
          onClose={() => setViewUserSelectModalOpen(false)}
          onSelectUser={handleSelectUser}
        />
      )}
    </>
  );
};
