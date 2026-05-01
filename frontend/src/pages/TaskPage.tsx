// src/pages/TaskPage.tsx
import { useEffect, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import { type TaskUserAccessLevel } from '@/api/generated/taskProgressAPI.schemas';

import { TaskControlPanel } from '@/components/task/TaskControlPanel';
import { TaskList } from '@/components/task/TaskList';
import type { PickedUser } from '@/components/task/ViewUserSelectModal/ViewUserSelectModal';

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
  const { user, loading: userLoading, getUserRole } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const [filterLevels, setFilterLevels] = useState(DEFAULT_FILTER);
  const [selectedUser, setSelectedUser] = useState<PickedUser | null>(null);
  const [isObjExpand, setIsObjExpand] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    const savedFilterLevels = loadFromLocalStorage();
    setFilterLevels(savedFilterLevels);
  }, []);

  useEffect(() => {
    if (userLoading) return;
    if (!user) {
      navigate('/login', { state: { from: location.pathname } });
    }
  }, [userLoading, user, navigate, location.pathname]);

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

  if (userLoading) return <p className="text-gray-500">読み込み中...</p>;
  if (!user) return null;
  return (
    <>
      <p className="font-bold text-lg mb-4">
        👤 {user.name} (ID: {user.id}) organization:( {user.organization_name}) 権限:(
        {String(getUserRole())})
      </p>
      <TaskControlPanel
        onAllExpand={onAllExpand}
        onAllCollapse={onAllCollapse}
        viewMode={filterLevels}
        onChangeViewMode={handleChangeViewMode}
        onSelectUser={handleSelectUser}
      />
      <TaskList isExpandParent={isObjExpand} viewMode={filterLevels} selectedUser={selectedUser} />
    </>
  );
};

export default function TaskPage() {
  return <TaskPageContent />;
}
