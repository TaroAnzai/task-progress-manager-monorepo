import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { usePostObjectives } from '@/api/generated/taskProgressAPI';

import { NewTaskModal } from '@/components/task/newTaskModal/NewTaskModal';

import { useTasks } from '@/context/useTasks';

const toastError = vi.fn();
vi.mock('sonner', () => ({ toast: { error: (...args: unknown[]) => toastError(...args), success: vi.fn() } }));
vi.mock('@/api/generated/taskProgressAPI', () => ({ usePostObjectives: vi.fn() }));
vi.mock('@/context/useTasks', () => ({ useTasks: vi.fn() }));
vi.mock('@/components/task/aiSuggestModal/AiSuggestModal', () => ({ AiSuggestModal: () => <div>AI suggestion</div> }));

const createTask = vi.fn();
const onClose = vi.fn();

describe('NewTaskModal', () => {
  beforeEach(() => {
    createTask.mockReset();
    onClose.mockReset();
    toastError.mockReset();
    vi.mocked(useTasks).mockReturnValue({ createTask, createTaskAsync: vi.fn() } as unknown as unknown as ReturnType<typeof useTasks>);
    vi.mocked(usePostObjectives).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof usePostObjectives>);
  });

  it('rejects a blank title without closing the dialog', async () => {
    const user = userEvent.setup();
    render(<NewTaskModal open onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: '"作成"' }));

    expect(toastError).toHaveBeenCalledWith('タイトルは必須です');
    expect(createTask).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('creates a trimmed task, clears its form, and closes', async () => {
    const user = userEvent.setup();
    render(<NewTaskModal open onClose={onClose} />);

    await user.type(screen.getByPlaceholderText('タスク名'), '  Release plan  ');
    await user.type(screen.getByPlaceholderText('タスクの説明'), ' details ');
    await user.click(screen.getByRole('button', { name: '"作成"' }));

    expect(createTask).toHaveBeenCalledWith({ title: 'Release plan', description: 'details', due_date: undefined });
    expect(onClose).toHaveBeenCalledOnce();
    expect(screen.getByPlaceholderText('タスク名')).toHaveValue('');
  });
});
