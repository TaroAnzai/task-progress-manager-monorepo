import { useEffect, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';

import { useGetCompaniesCompanyId } from '@/api/generated/taskProgressAPI';
import type { Company } from '@/api/generated/taskProgressAPI.schemas';

import { CompanyRegisterDialog } from '@/components/admin/CompanyRegisterDialog';
import { CompanySelectorDialog } from '@/components/admin/CompanySelectorDialog';
import { AdminOrganizationComponent } from '@/components/admin/organization/AdminOrganizationComponent';
import { UserSettingComponent } from '@/components/admin/user/UserSettingComponent';
import { AdminUserComponent } from '@/components/admin/users/AdminUserComponent';

import { useUser } from '@/context/useUser';

const AdminPageContent = () => {
  const { user, loading, hasAdminScope, getUserRole, refetchUser } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<Company | undefined>(undefined);

  const companyId = user?.company_id ?? null;

  const { data: companyData } = useGetCompaniesCompanyId(companyId ?? 0, undefined, {
    query: {
      enabled: !!companyId,
    },
  });

  useEffect(() => {
    if (companyData) {
      setSelectedCompany(companyData);
    }
  }, [companyData]);
  useEffect(() => {
    if (loading) return;
    if (!user) {
      navigate('/login', { state: { from: location.pathname } });
    }
  }, [loading, user, navigate, location.pathname]);

  if (loading) {
    return <p className="text-gray-500">読み込み中...</p>;
  }
  if (!user) {
    // レンダリングせず、リダイレクトが完了するまで何も表示しない
    return null;
  }
  return (
    <div className="p-4">
      <p className="font-bold text-lg mb-4">
        👤 {user.name} (ID: {user.id}) organization:( {user.organization_name}) 権限:(
        {String(getUserRole())})
      </p>
      <div className="flex justify-center space-y-6">
        <UserSettingComponent className="" user={user} refetchUser={refetchUser} />
      </div>

      {hasAdminScope() ? (
        <>
          {user.is_superuser && (
            <div className="space-y-6">
              <div className="p-4 border rounded bg-white shadow">
                <Button onClick={() => setDialogOpen(true)}>会社を選択</Button>
                <Button onClick={() => setSelectedCompany(undefined)}>会社選択解除</Button>
                <Button onClick={() => setRegisterOpen(true)}>会社を登録</Button>
                {selectedCompany && <p>選択中: {selectedCompany.name}</p>}
              </div>
            </div>
          )}

          {selectedCompany ? (
            <>
              <div className="space-y-6">
                <div className="p-4 border rounded bg-white shadow">
                  <div className="mt-4 space-y-2">
                    <AdminOrganizationComponent
                      companyName={selectedCompany.name}
                      companyId={selectedCompany.id}
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-6">
                <div className="p-4 border rounded bg-white shadow">
                  <div className="mt-4 space-y-2">
                    <AdminUserComponent companyId={selectedCompany.id!} />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-red-600 font-bold">⚠ 会社を選択してください。</p>
          )}
        </>
      ) : (
        <p className="text-red-600 font-bold">⚠ このページは管理者専用です。</p>
      )}
      {user.is_superuser && (
        <>
          <CompanySelectorDialog
            open={dialogOpen}
            onClose={() => setDialogOpen(false)}
            onSelect={(company) => setSelectedCompany(company)}
          />
          <CompanyRegisterDialog
            open={registerOpen}
            onClose={() => setRegisterOpen(false)}
            onSuccess={() => setSelectedCompany(undefined)} // useGetCompanies などで再取得
          />
        </>
      )}
    </div>
  );
};

export default function ProgressAdminPage() {
  return <AdminPageContent />;
}
