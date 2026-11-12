import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';

import { StatusBadgeCell } from '@/components/task/StatusBadgeCell';

describe('StatusBadgeCell', () => {
  it('allows selecting a status from a popover rendered over a modal', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <Dialog open>
        <DialogContent>
          <DialogTitle>オブジェクティブの一覧</DialogTitle>
          <DialogDescription>ステータス変更</DialogDescription>
          <StatusBadgeCell value="IN_PROGRESS" onChange={onChange} />
        </DialogContent>
      </Dialog>
    );

    await user.click(screen.getByRole('button', { name: '進行中' }));

    const completedOption = screen.getByRole('button', { name: '完了' });
    expect(completedOption.closest('[data-radix-popper-content-wrapper]')?.firstElementChild).toHaveStyle(
      { pointerEvents: 'auto' }
    );

    await user.click(completedOption);

    expect(onChange).toHaveBeenCalledWith('COMPLETED');
  });
});
