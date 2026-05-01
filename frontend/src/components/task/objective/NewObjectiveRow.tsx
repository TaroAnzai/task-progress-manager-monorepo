// src/components/task/ObjectiveRow.tsx

import { TableCell } from '@/components/ui/table';

import type { ObjectiveInput } from '@/api/generated/taskProgressAPI.schemas';

import { EditableCell } from './EditableCell';

interface NewObjectiveRowProps {
  taskId: number;
  onSaveNew: (obj: ObjectiveInput) => Promise<void>;
}

export const NewObjectiveRow = ({ taskId, onSaveNew }: NewObjectiveRowProps) => {
  const handleTitleSave = (newTitle: string) => {
    onSaveNew({ task_id: taskId, title: newTitle });
  };

  return (
    <>
      <TableCell className="w-8 px-2 py-2 select-none"></TableCell>
      <TableCell className="px-3 py-2">
        <EditableCell value={''} onSave={handleTitleSave} />
      </TableCell>
    </>
  );
};
