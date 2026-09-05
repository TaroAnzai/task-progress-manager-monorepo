import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useGetTasksTaskIdAuthorizedUsers } from '@/api/generated/taskProgressAPI';

import { SingleUserSelectModal } from '@/components/task/SingleUserSelectModal';

vi.mock('@/api/generated/taskProgressAPI', () => ({ useGetTasksTaskIdAuthorizedUsers: vi.fn() }));

const onClose = vi.fn();
const onConfirm = vi.fn();
const renderModal = () => render(<SingleUserSelectModal taskId={3} open onClose={onClose} onConfirm={onConfirm} excludedUserIds={[2]} />);

describe('SingleUserSelectModal', () => {
  beforeEach(() => { onClose.mockReset(); onConfirm.mockReset(); });

  it.each([
    [{ isLoading: true, isError: false }, '読み込み中...'],
    [{ isLoading: false, isError: true }, 'ユーザーの取得に失敗しました。'],
    [{ isLoading: false, isError: false, data: [] }, '該当するユーザーがいません。'],
  ])('renders the relevant async state', (state, message) => {
    vi.mocked(useGetTasksTaskIdAuthorizedUsers).mockReturnValue(state as ReturnType<typeof useGetTasksTaskIdAuthorizedUsers>);
    renderModal();
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  it('filters users, excludes existing users, and confirms one selection', async () => {
    const user = userEvent.setup();
    vi.mocked(useGetTasksTaskIdAuthorizedUsers).mockReturnValue({
      data: [
        { id: 1, name: 'Alice', organization_name: 'Engineering' },
        { id: 2, name: 'Bob', organization_name: 'Sales' },
        { id: 3, name: 'Carol', organization_name: 'Design' },
      ], isLoading: false, isError: false,
    } as ReturnType<typeof useGetTasksTaskIdAuthorizedUsers>);
    renderModal();

    expect(screen.queryByText('Bob')).not.toBeInTheDocument();
    const confirm = screen.getByRole('button', { name: '選択する' });
    expect(confirm).toBeDisabled();
    await user.type(screen.getByPlaceholderText('検索（名前）/ 組織名'), 'design');
    expect(screen.queryByText('Alice')).not.toBeInTheDocument();
    await user.click(screen.getByRole('radio', { name: /Carol/ }));
    await user.click(confirm);

    expect(onConfirm).toHaveBeenCalledWith({ id: 3, name: 'Carol' });
    expect(onClose).toHaveBeenCalledOnce();
  });
});
