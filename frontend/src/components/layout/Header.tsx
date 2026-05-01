// src/components/layout/Header.tsx

import { Link, useLocation } from 'react-router-dom';

import { useDeleteSessionsCurrent } from '@/api/generated/taskProgressAPI';

import { useUser } from '@/context/useUser';

export const Header = () => {
  const { user, refetchUser } = useUser();
  const isLoggedIn = !!user?.id;
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  const deleteSessionMutation = useDeleteSessionsCurrent();
  const handleLogout = async () => {
    try {
      await deleteSessionMutation.mutateAsync();
      refetchUser(); // ユーザー情報を更新（nullになる）
    } catch (error) {
      console.error('ログアウトに失敗しました', error);
    }
  };

  return (
    <header className="bg-gray-800 text-white p-4 flex justify-between items-center">
      <h1 className="text-lg font-bold">進捗管理システム Ver1.01</h1>
      <nav className="flex gap-4">
        <Link to="/" className="hover:underline">
          タスク一覧
        </Link>
        <Link to="admin" className="hover:underline">
          設定
        </Link>
        {isLoggedIn ? (
          <button onClick={handleLogout} className="hover:underline text-left">
            ログアウト
          </button>
        ) : (
          !isLoginPage && (
            <Link to="login" className="hover:underline">
              ログイン
            </Link>
          )
        )}
      </nav>
    </header>
  );
};
