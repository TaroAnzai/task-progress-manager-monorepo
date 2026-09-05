import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { UserContextType } from '@/context/UserContextBase';
import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';
import TaskPage from '@/pages/TaskPage';

vi.mock('@/context/useTasks', () => ({ useTasks: vi.fn() }));
vi.mock('@/context/useUser', () => ({ useUser: vi.fn() }));
vi.mock('@/components/task/TaskControlPanel', () => ({
  TaskControlPanel: () => <div>Task controls</div>,
}));
vi.mock('@/components/task/TaskList', () => ({
  TaskList: () => <div>Task list</div>,
}));

const user = {
  id: 1,
  organization_id: 10,
  organization_name: '開発部',
  company_id: 100,
  name: 'テストユーザー',
  email: 'test@example.com',
};

const createUserContext = (
  overrides: Partial<UserContextType> = {}
): UserContextType => ({
  user,
  loading: false,
  refetchUser: vi.fn(),
  hasAdminScope: vi.fn(() => false),
  hasSystemAdminScope: vi.fn(() => false),
  getUserRole: vi.fn(() => ''),
  ...overrides,
});

const renderTaskPage = () =>
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<TaskPage />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>
  );

describe('TaskPage', () => {
  beforeEach(() => {
    vi.mocked(useUser).mockReturnValue(createUserContext());
    vi.mocked(useTasks).mockReturnValue({ isLoading: false } as ReturnType<typeof useTasks>);
  });

  it('shows the loading status without rendering the normal content', () => {
    vi.mocked(useTasks).mockReturnValue({ isLoading: true } as ReturnType<typeof useTasks>);

    renderTaskPage();

    expect(screen.getByRole('status', { name: '読み込み中' })).toBeInTheDocument();
    expect(screen.queryByText('Task controls')).not.toBeInTheDocument();
    expect(screen.queryByText('Task list')).not.toBeInTheDocument();
  });

  it('removes the loading status and renders the normal content after loading', () => {
    vi.mocked(useTasks).mockReturnValue({ isLoading: true } as ReturnType<typeof useTasks>);
    const { rerender } = renderTaskPage();

    expect(screen.getByRole('status', { name: '読み込み中' })).toBeInTheDocument();

    vi.mocked(useTasks).mockReturnValue({ isLoading: false } as ReturnType<typeof useTasks>);
    rerender(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<TaskPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByRole('status', { name: '読み込み中' })).not.toBeInTheDocument();
    expect(screen.getByText('Task controls')).toBeInTheDocument();
    expect(screen.getByText('Task list')).toBeInTheDocument();
    expect(screen.getByText(/テストユーザー/)).toBeInTheDocument();
  });

  it('keeps the existing unauthenticated redirect behavior', async () => {
    vi.mocked(useUser).mockReturnValue(createUserContext({ user: null }));

    renderTaskPage();

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument());
    expect(screen.queryByRole('status', { name: '読み込み中' })).not.toBeInTheDocument();
  });
});
