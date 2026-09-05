import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useGetSessionsCurrent } from '@/api/generated/taskProgressAPI';
import { AccessScopeRole } from '@/api/generated/taskProgressAPI.schemas';

import { UserProvider } from '@/context/UserProvider';
import { useUser } from '@/context/useUser';

vi.mock('@/api/generated/taskProgressAPI', () => ({ useGetSessionsCurrent: vi.fn() }));

const Consumer = () => {
  const { user, loading, sessionError, hasAdminScope, hasSystemAdminScope, getUserRole } = useUser();
  return <div>{JSON.stringify({ id: user?.id ?? null, loading, sessionError: !!sessionError, admin: hasAdminScope(), system: hasSystemAdminScope(), role: getUserRole() })}</div>;
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

  it('stops loading and exposes an error when the session request fails', async () => {
    vi.mocked(useGetSessionsCurrent).mockReturnValue({
      error: new Error('network error'), isLoading: false, isFetching: false,
      isSuccess: false, isError: true, refetch: vi.fn(),
    } as unknown as ReturnType<typeof useGetSessionsCurrent>);
    render(<UserProvider><Consumer /></UserProvider>);
    expect(await screen.findByText(/"id":null,"loading":false,"sessionError":true/)).toBeInTheDocument();
  });

  it('keeps the authenticated user when a background refetch fails', async () => {
    const authenticatedResult = {
      data: { id: 9, name: 'Admin' }, isLoading: false, isFetching: false,
      isSuccess: true, isError: false, error: null, refetch: vi.fn(),
    } as unknown as ReturnType<typeof useGetSessionsCurrent>;
    vi.mocked(useGetSessionsCurrent).mockReturnValue(authenticatedResult);
    const { rerender } = render(<UserProvider><Consumer /></UserProvider>);
    expect(await screen.findByText(/"id":9,"loading":false,"sessionError":false/)).toBeInTheDocument();

    vi.mocked(useGetSessionsCurrent).mockReturnValue({
      ...authenticatedResult, data: undefined, isSuccess: false, isError: true,
      error: new Error('temporary error'),
    } as unknown as ReturnType<typeof useGetSessionsCurrent>);
    rerender(<UserProvider><Consumer /></UserProvider>);
    expect(await screen.findByText(/"id":9,"loading":false,"sessionError":true/)).toBeInTheDocument();
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
