// src/pages/TaskPage.tsx
import { useEffect, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';
import { ClipLoader } from 'react-spinners';

import { Button } from '@/components/ui/button';

import { type TaskUserAccessLevel } from '@/api/generated/taskProgressAPI.schemas';

import { TaskControlPanel } from '@/components/task/TaskControlPanel';
import { TaskList } from '@/components/task/TaskList';
import type { PickedUser } from '@/components/task/ViewUserSelectModal/ViewUserSelectModal';

import { getRoleLabelJa } from '@/context/roleLabels';
import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';

const STORAGE_KEY = 'task_view_mode';
export type FilterAccessLevel = TaskUserAccessLevel | 'ASSIGNED';
const DEFAULT_FILTER: Record<FilterAccessLevel, boolean> = {
  VIEW: true,
  EDIT: true,
  FULL: true,
  OWNER: true,
  ASSIGNED: true,
};

const loadFromLocalStorage = (): Record<FilterAccessLevel, boolean> => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      return parsed;
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return DEFAULT_FILTER;
    }
  }
  return DEFAULT_FILTER;
};
const TaskPageContent = () => {
  const { user, loading: userLoading, sessionError, refetchUser, getUserRole } = useUser();
  const { isLoading: tasksLoading } = useTasks();
  const navigate = useNavigate();
  const location = useLocation();
  const [filterLevels, setFilterLevels] = useState(DEFAULT_FILTER);
  const [selectedUser, setSelectedUser] = useState<PickedUser | null>(null);
  const [isObjExpand, setIsObjExpand] = useState<boolean | undefined>(undefined);

  // 画面遷移時に保存した表示フィルターを復元
  useEffect(() => {
    const savedFilterLevels = loadFromLocalStorage();
    setFilterLevels(savedFilterLevels);
  }, []);
  // ログインしていない場合はログイン画面に遷移
  useEffect(() => {
    if (userLoading || sessionError) return;
    if (!user) {
      navigate('/login', { state: { from: location.pathname } });
    }
  }, [userLoading, sessionError, user, navigate, location.pathname]);

  const onAllExpand = () => {
    setIsObjExpand(true);
  };
  const onAllCollapse = () => {
    setIsObjExpand(false);
  };

  const handleChangeViewMode = (newValue: Record<FilterAccessLevel, boolean>) => {
    setFilterLevels(newValue);
    setSelectedUser(null);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newValue));
  };
  const handleSelectUser = (user: PickedUser | null) => {
    setSelectedUser(user);
    const savedFilterLevels = loadFromLocalStorage();
    if (user === null) {
      setFilterLevels(savedFilterLevels);
    } else {
      setFilterLevels(DEFAULT_FILTER);
    }
  };

  if (userLoading || (!sessionError && user && tasksLoading)) {
    return (
      <div
        className="flex h-full min-h-64 w-full flex-col items-center justify-center gap-4"
        role="status"
        aria-label="読み込み中"
        aria-live="polite"
      >
        <ClipLoader color="#36d7b7" size={72} aria-hidden="true" />
        <span className="text-sm text-gray-500">読み込み中...</span>
      </div>
    );
  }
  if (sessionError) {
    return (
      <div className="flex h-full min-h-64 w-full flex-col items-center justify-center gap-4 text-center">
        <p>認証状態を確認できませんでした。通信状況を確認して、もう一度お試しください。</p>
        <Button type="button" onClick={refetchUser}>
          再試行
        </Button>
      </div>
    );
  }
  if (!user) return null;
  return (
    <div className="flex h-full min-h-0 flex-col">
      <p className="font-bold text-lg mb-1">
        👤 {user.name} (ID: {user.id}) 所属組織:( {user.organization_name}) 権限:(
        {getRoleLabelJa(getUserRole())} )
      </p>
      <TaskControlPanel
        onAllExpand={onAllExpand}
        onAllCollapse={onAllCollapse}
        viewMode={filterLevels}
        onChangeViewMode={handleChangeViewMode}
        onSelectUser={handleSelectUser}
      />
      <TaskList isExpandParent={isObjExpand} viewMode={filterLevels} selectedUser={selectedUser} />
    </div>
  );
};

export default function TaskPage() {
  return <TaskPageContent />;
}
