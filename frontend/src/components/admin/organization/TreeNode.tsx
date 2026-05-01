import React, { useState } from 'react';

import { toast } from 'sonner';

import {
  useDeleteOrganizationsOrgId,
  usePostOrganizations,
  usePutOrganizationsOrgId,
} from '@/api/generated/taskProgressAPI';
import type { OrganizationTree } from '@/api/generated/taskProgressAPI.schemas';

import { extractErrorMessage } from '@/utils/errorHandler';

interface TreeNodeProps {
  node: OrganizationTree;
  onRefresh: () => void;
}

export const TreeNode: React.FC<TreeNodeProps> = ({ node, onRefresh }) => {
  const [open, setOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [childName, setChildName] = useState('');
  const [childCode, setChildCode] = useState('');

  const createOrgMutation = usePostOrganizations();
  const deleteOrgMutation = useDeleteOrganizationsOrgId();
  const updateParentMutation = usePutOrganizationsOrgId();

  const handleAddChild = async () => {
    if (!childName || !childCode) {
      toast.error('組織名とコードは必須です');
      return;
    }

    try {
      await createOrgMutation.mutateAsync({
        data: {
          name: childName,
          org_code: childCode,
          parent_id: node.id,
          company_id: node.company_id!,
        },
      });
      toast.success(`${childName} を追加しました`);
      setAdding(false);
      setChildName('');
      setChildCode('');
      onRefresh();
    } catch (e) {
      toast.error(`${extractErrorMessage(e)}`);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`「${node.name}」を削除しますか？`)) return;

    if (!node.id) {
      toast.error('IDが見つかりません');
      return;
    }

    try {
      await deleteOrgMutation.mutateAsync({ orgId: node.id });
      await deleteOrgMutation.mutateAsync({ orgId: node.id });
      toast.success(`${node.name} を削除しました`);
      onRefresh();
    } catch (e) {
      toast.error(`削除失敗: ${extractErrorMessage(e)}`);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation(); // ← これを追加
    const draggedIdStr = e.dataTransfer.getData('text/plain');
    const draggedId = parseInt(draggedIdStr, 10);

    if (!draggedIdStr || isNaN(draggedId) || draggedId === node.id) return;

    if (!node.id) {
      toast.error('ドロップ先のIDが見つかりません');
      return;
    }

    try {
      await updateParentMutation.mutateAsync({
        orgId: draggedId,
        data: { parent_id: node.id },
      });
      toast.success('親組織を更新しました');
      onRefresh();
    } catch (e) {
      toast.error(`登録に失敗しました: ${extractErrorMessage(e)}`);
    }
  };

  return (
    <li
      draggable
      onDragStart={(e) => {
        e.stopPropagation();
        e.dataTransfer.setData('text/plain', String(node.id));
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      className="pl-2"
    >
      <span className="cursor-pointer select-none" onClick={() => setOpen((prev) => !prev)}>
        {node.children && node.children.length > 0 ? (open ? '▼' : '▶') : '・'}
      </span>
      <span className="ml-1">
        {node.name} ({node.org_code})
      </span>
      <span className="ml-2 space-x-1">
        <button onClick={handleDelete} className="text-red-500 hover:text-red-700">
          ×
        </button>
        <button
          onClick={() => setAdding((a) => !a)}
          className="text-green-500 hover:text-green-700"
        >
          ＋
        </button>
      </span>

      {adding && (
        <div className="ml-4 mt-1 space-x-1">
          <input
            className="border rounded p-1"
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            placeholder="組織名"
          />
          <input
            className="border rounded p-1"
            value={childCode}
            onChange={(e) => setChildCode(e.target.value)}
            placeholder="組織コード"
          />
          <button onClick={handleAddChild} className="px-1 py-0.5 bg-blue-500 text-white rounded">
            登録
          </button>
          <button onClick={() => setAdding(false)} className="px-1 py-0.5 bg-gray-300 rounded">
            キャンセル
          </button>
        </div>
      )}

      {open && node.children && node.children.length > 0 && (
        <ul className="list-none pl-4">
          {node.children.map((child) => (
            <TreeNode key={child.org_code} node={child} onRefresh={onRefresh} />
          ))}
        </ul>
      )}
    </li>
  );
};
