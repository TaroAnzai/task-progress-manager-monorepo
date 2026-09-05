import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { usePostSessions } from '@/api/generated/taskProgressAPI';

import { useAlertDialog } from '@/context/useAlertDialog';
import { useUser } from '@/context/useUser';
import LoginPage from '@/pages/LoginPage';

vi.mock('@/api/generated/taskProgressAPI', () => ({ usePostSessions: vi.fn() }));
vi.mock('@/context/useAlertDialog', () => ({ useAlertDialog: vi.fn() }));
vi.mock('@/context/useUser', () => ({ useUser: vi.fn() }));

const openAlertDialog = vi.fn();
const refetchUser = vi.fn();
let mutationOptions: Record<string, (...args: unknown[]) => unknown>;
let mutate: ReturnType<typeof vi.fn>;

const renderLogin = (entry: string | { pathname: string; state?: unknown } = '/login') =>
  render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/private" element={<div>Private page</div>} />
      </Routes>
    </MemoryRouter>
  );

describe('LoginPage', () => {
  beforeEach(() => {
    mutate = vi.fn();
    openAlertDialog.mockReset();
    refetchUser.mockReset();
    vi.mocked(useAlertDialog).mockReturnValue({ openAlertDialog });
    vi.mocked(useUser).mockReturnValue({ refetchUser } as unknown as ReturnType<typeof useUser>);
    vi.mocked(usePostSessions).mockImplementation((options) => {
      mutationOptions = options!.mutation as typeof mutationOptions;
      return { mutate, isPending: false } as unknown as ReturnType<typeof usePostSessions>;
    });
  });

  it('disables submission until both credentials are entered and submits trimmed email', async () => {
    const user = userEvent.setup();
    renderLogin();
    const submit = screen.getByRole('button', { name: /^ログイン$/ });

    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText('メールアドレス'), '  user@example.com  ');
    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText('パスワード'), 'secret');
    expect(submit).toBeEnabled();
    await user.click(submit);

    expect(mutate).toHaveBeenCalledWith({
      data: { email: 'user@example.com', password: 'secret' },
    });
  });

  it('refetches authentication and returns to the requested page after success', async () => {
    refetchUser.mockResolvedValue(undefined);
    renderLogin({ pathname: '/login', state: { from: '/private' } });

    await act(async () => mutationOptions.onSuccess());

    expect(refetchUser).toHaveBeenCalledOnce();
    expect(await screen.findByText('Private page')).toBeInTheDocument();
  });

  it('shows API and OIDC login failures through the shared alert dialog', async () => {
    renderLogin('/login?oidc_error=user_not_registered');

    await waitFor(() => expect(openAlertDialog).toHaveBeenCalledWith(expect.objectContaining({
      title: 'ログインエラー',
      description: expect.stringContaining('利用登録がありません'),
    })));

    openAlertDialog.mockClear();
    mutationOptions.onError(new Error('invalid credentials'));
    expect(openAlertDialog).toHaveBeenCalledWith(expect.objectContaining({
      title: 'エラー',
      description: expect.stringContaining('ログイン失敗'),
    }));
  });
});
