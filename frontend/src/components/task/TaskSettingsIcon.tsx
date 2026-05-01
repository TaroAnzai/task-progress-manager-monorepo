// src/components/task/TaskSettingsIcon.tsx
import { useState } from 'react';

import { Settings } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import type { Task } from '@/api/generated/taskProgressAPI.schemas';

import { ObjectiveListModal } from './objectiveListModal/ObjectiveListModal';
import { TaskScopeModal } from './taskScopeModal/TaskScopeModal.tsx';
import { TaskSettingModal } from './taskSettingModal/TaskSettingModal';

interface TaskSettingsIconProps {
  task: Task;
  isUpdateTask: boolean;
}

export const TaskSettingsIcon = ({ task, isUpdateTask }: TaskSettingsIconProps) => {
  const [openSetting, setOpenSetting] = useState(false);
  const [openScope, setOpenScope] = useState(false);
  const [openObjectiveModal, setOpenObjectiveModal] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleOpenSetting = (e:Event) => {
    e.preventDefault();
    setDropdownOpen(false);
    setTimeout(() => setOpenSetting(true), 0);
  };

  const handleOpenScope = (e:Event) => {
    e.preventDefault();
    setDropdownOpen(false);
    setTimeout(() => setOpenScope(true), 0);
  };

  const handleOpenObjectiveModal = (e:Event) => {
    e.preventDefault();
    setDropdownOpen(false);
    setTimeout(() => setOpenObjectiveModal(true), 0);
  };



  return (
    <>
      <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-600 hover:text-gray-900"
            title="設定"
          >
            <Settings className="h-5 w-5" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-44">
          <DropdownMenuItem disabled={!isUpdateTask} onSelect={handleOpenSetting}>
            設定
          </DropdownMenuItem>
          <DropdownMenuItem disabled={!isUpdateTask} onSelect={handleOpenScope}>
            スコープ設定
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={handleOpenObjectiveModal}>
            オブジェクティブ一覧
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 設定モーダル */}

        <TaskSettingModal open={openSetting} task={task} onClose={() => setOpenSetting(false)} />

      {/* スコープ設定モーダル */}

        <TaskScopeModal open={openScope} task={task} onClose={() => setOpenScope(false)} />


      {/* オブジェクティブ一覧モーダル */}

        <ObjectiveListModal
          open={openObjectiveModal}
          task={task}
          onClose={() => setOpenObjectiveModal(false)}
          canUpdate={isUpdateTask}
        />

    </>
  );
};
