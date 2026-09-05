import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useGetSessionsCurrent } from '@/api/generated/taskProgressAPI';
import { AccessScopeRole } from '@/api/generated/taskProgressAPI.schemas';

import { UserProvider } from '@/context/UserProvider';
import { useUser } from '@/context/useUser';

vi.mock('@/api/generated/taskProgressAPI', () => ({ useGetSessionsCurrent: vi.fn() }));

const Consumer = () => {
  const { user, loading, hasAdminScope, hasSystemAdminScope, getUserRole } = useUser();
  return <div>{JSON.stringify({ id: user?.id ?? null, loading, admin: hasAdminScope(), system: hasSystemAdminScope(), role: getUserRole() })}</div>;
};

describe('UserProvider', () => {
  beforeEach(() => vi.mocked(useGetSessionsCurrent).mockReset());

  it('keeps the authentication state loading while the session request is pending', () => {
    vi.mocked(useGetSessionsCurrent).mockReturnValue({ isLoading: true, isFetching: true, isSuccess: false, refetch: vi.fn() } as unknown as ReturnType<typeof useGetSessionsCurrent>);
    render(<UserProvider><Consumer /></UserProvider>);
    expect(screen.getByText(/"loading":true/)).toBeInTheDocument();
  });

  it('maps an empty successful session to an unauthenticated user', async () => {
    vi.mocked(useGetSessionsCurrent).mockReturnValue({ data: undefined, isLoading: false, isFetching: false, isSuccess: true, refetch: vi.fn() } as unknown as ReturnType<typeof useGetSessionsCurrent>);
    render(<UserProvider><Consumer /></UserProvider>);
    expect(await screen.findByText(/"id":null,"loading":false/)).toBeInTheDocument();
  });

  it('derives system administrator permissions from access scopes', async () => {
    vi.mocked(useGetSessionsCurrent).mockReturnValue({
      data: { id: 9, name: 'Admin', access_scopes: [{ role: AccessScopeRole.SYSTEM_ADMIN }] },
      isLoading: false, isFetching: false, isSuccess: true, refetch: vi.fn(),
    } as unknown as ReturnType<typeof useGetSessionsCurrent>);
    render(<UserProvider><Consumer /></UserProvider>);
    expect(await screen.findByText(/"admin":true,"system":true,"role":"system-admin"/)).toBeInTheDocument();
  });
});
