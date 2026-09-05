/* eslint-disable @typescript-eslint/no-explicit-any */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as generated from '@/api/generated/taskProgressAPI';
import { TaskUserAccessLevel } from '@/api/generated/taskProgressAPI.schemas';

import { TaskProvider } from '@/context/TaskProvider';
import { useAlertDialog } from '@/context/useAlertDialog';
import { useTasks } from '@/context/useTasks';
import { useUser } from '@/context/useUser';

vi.mock('@/api/generated/taskProgressAPI', () => ({
  getGetTasksQueryOptions: () => ({ queryKey: ['tasks'] }),
  getGetTasksTaskIdQueryOptions: (id: number) => ({ queryKey: ['tasks', id] }),
  useGetTasks: vi.fn(), usePostTasks: vi.fn(), usePutTasksTaskId: vi.fn(),
  usePostTaskOrders: vi.fn(), useDeleteTasksTaskId: vi.fn(),
}));
vi.mock('@/context/useUser', () => ({ useUser: vi.fn() }));
vi.mock('@/context/useAlertDialog', () => ({ useAlertDialog: vi.fn() }));
vi.mock('sonner', () => ({ toast: { success: vi.fn() } }));

const alert = vi.fn();
let createOptions: any;
let updateOptions: any;

const Consumer = () => {
  const { tasks, createTask, updateTask, can } = useTasks();
  return <><div>{tasks.map((task) => task.title).join(',')}</div><div>{can('task.update', { taskId: 1 }) ? 'editable' : 'readonly'}</div><button onClick={() => createTask({ title: 'New' })}>create</button><button onClick={() => updateTask(1, { title: 'Changed' })}>update</button></>;
};

describe('TaskProvider', () => {
  let queryClient: QueryClient;
  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    alert.mockReset();
    vi.mocked(useUser).mockReturnValue({ user: { id: 7 } } as unknown as ReturnType<typeof useUser>);
    vi.mocked(useAlertDialog).mockReturnValue({ openAlertDialog: alert });
    vi.mocked(generated.useGetTasks).mockReturnValue({ data: { tasks: [{ id: 1, title: 'Original', user_access_level: TaskUserAccessLevel.FULL }] }, isLoading: false, refetch: vi.fn() } as unknown as ReturnType<typeof generated.useGetTasks>);
    vi.mocked(generated.usePostTasks).mockImplementation((options) => { createOptions = options!.mutation; return { mutate: (vars: unknown) => createOptions.onSuccess({ task: { id: 2, title: (vars as any).data.title } }), mutateAsync: vi.fn() } as unknown as ReturnType<typeof generated.usePostTasks>; });
    vi.mocked(generated.usePutTasksTaskId).mockImplementation((options) => { updateOptions = options!.mutation; return { mutate: vi.fn() } as unknown as ReturnType<typeof generated.usePutTasksTaskId>; });
    vi.mocked(generated.usePostTaskOrders).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof generated.usePostTaskOrders>);
    vi.mocked(generated.useDeleteTasksTaskId).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof generated.useDeleteTasksTaskId>);
  });

  const renderProvider = () => render(<QueryClientProvider client={queryClient}><TaskProvider><Consumer /></TaskProvider></QueryClientProvider>);

  it('exposes access control and inserts a successfully created task into the query cache', async () => {
    const user = userEvent.setup();
    renderProvider();
    expect(screen.getByText('editable')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'create' }));
    expect(queryClient.getQueryData<{ tasks: Array<{ title: string }> }>(['tasks'])?.tasks[0].title).toBe('New');
  });

  it('rolls an optimistic task update back and reports the API error', () => {
    queryClient.setQueryData(['tasks'], { tasks: [{ id: 1, title: 'Original' }] });
    queryClient.setQueryData(['tasks', 1], { id: 1, title: 'Original' });
    renderProvider();
    const variables = { taskId: 1, data: { title: 'Changed' } };
    const context = updateOptions.onMutate(variables);
    expect(queryClient.getQueryData<{ title: string }>(['tasks', 1])?.title).toBe('Changed');
    updateOptions.onError(new Error('network'), variables, context);
    expect(queryClient.getQueryData<{ title: string }>(['tasks', 1])?.title).toBe('Original');
    expect(alert).toHaveBeenCalledWith(expect.objectContaining({ title: 'タスク更新に失敗しました' }));
  });
});
