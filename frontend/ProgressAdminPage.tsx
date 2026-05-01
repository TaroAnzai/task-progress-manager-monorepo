import { useEffect, useState } from "react";
import { UserProvider, useUser } from "../context/UserContext";

function AdminPageContent() {
  const { user, loading } = useGetProgressSessionsCurrent();

  if (loading) {
    return <p className="text-gray-500">読み込み中...</p>;
  }

  if (!user) {
    return (
      <div className="p-4">
        <p className="text-red-600 font-bold mb-2">⚠ ログインしてください。</p>
      </div>
    );
  }

  const isAdmin = user.scopes?.some((s: any) => ["system_admin", "admin"].includes(s.role));

  return (
    <div className="p-4">
      <p className="font-bold text-lg mb-4">👤 {user.name} (ID: {user.id})</p>

      {isAdmin ? (
        <div className="space-y-6">
          {/* ✅ 後でOrganizationAdmin, UserAdminコンポーネントを追加予定 */}
          <div className="p-4 border rounded bg-white shadow">
            <p className="text-gray-700">管理者用コンテンツはここに表示されます。</p>
          </div>
        </div>
      ) : (
        <p className="text-red-600 font-bold">⚠ このページは管理者専用です。</p>
      )}
    </div>
  );
}

export default function ProgressAdminPage() {
  return (
    <UserProvider>
      <AdminPageContent />
    </UserProvider>
  );
}
