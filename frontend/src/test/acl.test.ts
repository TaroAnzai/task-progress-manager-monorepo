import { describe, expect, it } from 'vitest';

import { can } from '@/acl/can';

const objective = (assignedUserId?: number) =>
  ({ id: 10, task_id: 1, assigned_user_id: assignedUserId }) as Parameters<typeof can>[1];

describe('task permissions', () => {
  it('allows actions that match the task access level', () => {
    expect(can('task.view', { taskId: 1 }, () => 'VIEW', 7)).toBe(true);
    expect(can('objective.update', objective(), () => 'EDIT', 7)).toBe(true);
    expect(can('task.delete', { taskId: 1 }, () => 'EDIT', 7)).toBe(false);
  });

  it('lets an assigned user record progress even with view-only access', () => {
    expect(can('progress.create', objective(7), () => 'VIEW', 7)).toBe(true);
    expect(can('progress.update', objective(8), () => 'VIEW', 7)).toBe(false);
    expect(can('progress.delete', objective(7), () => 'VIEW', 7)).toBe(false);
  });
});
