import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  useDeleteObjectivesObjectiveId,
  useGetObjectivesTasksTaskId,
  usePutObjectivesObjectiveId,
} from '@/api/generated/taskProgressAPI';
import type { Objective, Task } from '@/api/generated/taskProgressAPI.schemas';

import { ObjectiveListModal } from '@/components/task/objectiveListModal/ObjectiveListModal';

import { useTasks } from '@/context/useTasks';

vi.mock('@/api/generated/taskProgressAPI', () => ({
  getGetObjectivesTasksTaskIdQueryOptions: (taskId: number) => ({
    queryKey: ['objectives', taskId],
  }),
  useDeleteObjectivesObjectiveId: vi.fn(),
  useGetObjectivesTasksTaskId: vi.fn(),
  usePutObjectivesObjectiveId: vi.fn(),
}));
vi.mock('@/context/useAlertDialog', () => ({
  useAlertDialog: () => ({ openAlertDialog: vi.fn() }),
}));
vi.mock('@/context/useTasks', () => ({ useTasks: vi.fn() }));
vi.mock('@/components/task/StatusBadgeCell', () => ({
  StatusBadgeCell: ({
    value,
    disabled,
    onChange,
  }: {
    value: string;
    disabled?: boolean;
    onChange?: (status: 'COMPLETED') => void;
  }) => (
    <button disabled={disabled} onClick={() => onChange?.('COMPLETED')}>
      status-{value}
    </button>
  ),
}));

const task = { id: 10, title: 'Task' } as Task;
const objective = {
  id: 20,
  task_id: task.id,
  title: 'Objective',
  status: 'IN_PROGRESS',
} as Objective;

const updateObjective = vi.fn();
const deleteObjective = vi.fn();
let updateMutationOptions: {
  onMutate?: (variables: {
    objectiveId: number;
    data: { status: 'COMPLETED' };
  }) => Promise<unknown>;
};

const renderModal = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const result = render(
    <QueryClientProvider client={queryClient}>
      <ObjectiveListModal open task={task} onClose={vi.fn()} />
    </QueryClientProvider>
  );
  return { ...result, queryClient };
};

describe('ObjectiveListModal permissions', () => {
  beforeEach(() => {
    updateObjective.mockReset();
    deleteObjective.mockReset();
    vi.mocked(useGetObjectivesTasksTaskId).mockImplementation(
      () =>
        useQuery({
          queryKey: ['objectives', task.id],
          queryFn: () => Promise.resolve({ objectives: [objective] }),
          initialData: { objectives: [objective] },
        }) as ReturnType<typeof useGetObjectivesTasksTaskId>
    );
    vi.mocked(usePutObjectivesObjectiveId).mockImplementation((options) => {
      updateMutationOptions = options?.mutation as typeof updateMutationOptions;
      updateObjective.mockImplementation(async (variables) => {
        await updateMutationOptions.onMutate?.(variables);
      });
      return { mutate: updateObjective } as unknown as ReturnType<
        typeof usePutObjectivesObjectiveId
      >;
    });
    vi.mocked(useDeleteObjectivesObjectiveId).mockReturnValue({
      mutate: deleteObjective,
    } as unknown as ReturnType<typeof useDeleteObjectivesObjectiveId>);
  });

  it('allows an EDIT user to update an objective status and reflects it in the modal', async () => {
    const can = vi.fn((action: string) =>
      ['objective.update', 'objective.delete'].includes(action)
    );
    vi.mocked(useTasks).mockReturnValue({ can } as unknown as ReturnType<typeof useTasks>);

    renderModal();
    const statusButton = screen.getByRole('button', { name: 'status-IN_PROGRESS' });

    expect(statusButton).toBeEnabled();
    expect(screen.getByRole('button', { name: '削除' })).toBeEnabled();
    fireEvent.click(statusButton);
    expect(can).toHaveBeenCalledWith('objective.update', objective);
    expect(updateObjective).toHaveBeenCalledWith({
      objectiveId: objective.id,
      data: { status: 'COMPLETED' },
    });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'status-COMPLETED' })).toBeEnabled();
    });
  });

  it('keeps objective actions disabled for a VIEW user', () => {
    vi.mocked(useTasks).mockReturnValue({
      can: vi.fn(() => false),
    } as unknown as ReturnType<typeof useTasks>);

    renderModal();

    expect(screen.getByRole('button', { name: 'status-IN_PROGRESS' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '削除' })).toBeDisabled();
  });
});
