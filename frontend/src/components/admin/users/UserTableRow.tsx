// src/components/admin/user/UserTableRow.tsx

import React from 'react';

import { Button } from '@/components/ui/button';
import { TableCell, TableRow } from '@/components/ui/table';

import type { UserSchemaForAdmin } from '@/api/generated/taskProgressAPI.schemas';

import { ROLE_LABELS } from '@/context/roleLabels';

interface Props {
  user: UserSchemaForAdmin;
  onEdit: () => void;
  onDelete: () => void;
}

export const UserTableRow: React.FC<Props> = ({ user, onEdit, onDelete }) => {
  const visibleScopes = user.access_scopes?.filter(s => s.organization_id === user.organization_id) || [];
  const scopeDisplay = visibleScopes.length > 0
    ? visibleScopes.map(s => ROLE_LABELS[s.role] ?? s.role).join(', ')
    : '未設定';

  return (
    <TableRow onClick={onEdit} className="cursor-pointer hover:bg-muted/50">
      <TableCell>{user.name}</TableCell>
      <TableCell>{user.email}</TableCell>
      <TableCell>{user.organization_name ?? '未設定'}</TableCell>
      <TableCell>{scopeDisplay}</TableCell>
      <TableCell>{user.wp_user_id != null ? '〇' : ''}</TableCell>
      <TableCell>
        <Button variant="destructive" size="sm" onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}>
          削除
        </Button>
      </TableCell>
    </TableRow>
  );
};


