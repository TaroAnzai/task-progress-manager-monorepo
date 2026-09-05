import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { usePostAuthPasswordResetConfirm } from '@/api/generated/taskProgressAPI';

import { useAlertDialog } from '@/context/useAlertDialog';
import PasswordConfirmPage from '@/pages/PasswordConfirmPage';

vi.mock('@/api/generated/taskProgressAPI', () => ({
  usePostAuthPasswordResetConfirm: vi.fn(),
}));
vi.mock('@/context/useAlertDialog', () => ({ useAlertDialog: vi.fn() }));

const renderPasswordConfirmPage = () =>
  render(
    <MemoryRouter initialEntries={['/reset-password?token=test-token']}>
      <Routes>
        <Route path="/reset-password" element={<PasswordConfirmPage />} />
        <Route path="/reset" element={<div>パスワード再設定要求画面</div>} />
        <Route path="/login" element={<div>ログイン画面</div>} />
      </Routes>
    </MemoryRouter>
  );

describe('PasswordConfirmPage', () => {
  beforeEach(() => {
    vi.mocked(useAlertDialog).mockReturnValue({
      openAlertDialog: vi.fn(),
    });
    vi.mocked(usePostAuthPasswordResetConfirm).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof usePostAuthPasswordResetConfirm>);
  });

  it('renders from the password confirmation URL and navigates to the reset request page', async () => {
    const user = userEvent.setup();
    renderPasswordConfirmPage();

    expect(screen.getByText('パスワードの再設定')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '再設定メールを送る' }));

    expect(screen.getByText('パスワード再設定要求画面')).toBeInTheDocument();
  });

  it('navigates back to the login page', async () => {
    const user = userEvent.setup();
    renderPasswordConfirmPage();

    await user.click(screen.getByRole('button', { name: 'ログインへ戻る' }));

    expect(screen.getByText('ログイン画面')).toBeInTheDocument();
  });
});
