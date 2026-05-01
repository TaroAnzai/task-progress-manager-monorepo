import { type ReactNode, useEffect, useState } from 'react';

import { useGetSessionsCurrent } from '@/api/generated/taskProgressAPI';
import { AccessScopeRole, type UserWithScopes } from '@/api/generated/taskProgressAPI.schemas';

import { UserContext } from './UserContextBase';

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const {
    data: sessionData,
    isLoading,
    isFetching,
    isSuccess,
    refetch,
  } = useGetSessionsCurrent();

  const [user, setUser] = useState<UserWithScopes | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoading && !isFetching && isSuccess) {
      const u = sessionData as UserWithScopes | undefined;
      setUser(u && u.id ? u : null);
      setLoading(false);
    }
  }, [isLoading, isFetching, isSuccess, sessionData]);

  const hasSystemAdminScope = (): boolean =>
    !!user?.access_scopes?.some((s) => s.role === AccessScopeRole.SYSTEM_ADMIN);

  const hasAdminScope = (): boolean =>
    !!(
      user?.is_superuser ||
      user?.access_scopes?.some(
        (s) => s.role === AccessScopeRole.SYSTEM_ADMIN || s.role === AccessScopeRole.ORG_ADMIN
      )
    );

  const getUserRole = (): string => {
    if (user?.is_superuser) return 'Superuser';
    if (hasSystemAdminScope()) return 'system-admin';
    if (hasAdminScope()) return 'organization-admin';
    return '';
  };

  return (
    <UserContext.Provider
      value={{
        user,
        loading,
        refetchUser: refetch,
        hasAdminScope,
        hasSystemAdminScope,
        getUserRole,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};
