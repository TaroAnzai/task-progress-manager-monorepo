import { useEffect, useRef, useState } from 'react';

import type {
  ObjectiveUpdateStatus as updateStatusType,
  ProgressStatus as StatusType,
  TaskStatus,
  TaskUpdateStatus,
} from '@/api/generated/taskProgressAPI.schemas';
type Props = {
  value: StatusType | TaskStatus;
  onChange?: (newStatus: updateStatusType | TaskUpdateStatus) => void;
  disabled?: boolean;
};
export const StatusBadgeCell = ({ value, onChange, disabled = false }: Props) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const currentStatus = value || 'UNDEFINED';

  const STATUS_LABELS = {
    UNDEFINED: '未定義',
    NOT_STARTED: '未着手',
    IN_PROGRESS: '進行中',
    COMPLETED: '完了',
    SAVED: '保存',
  };

  const STATUS_COLORS = {
    UNDEFINED: 'bg-gray-300',
    NOT_STARTED: 'bg-gray-400',
    IN_PROGRESS: 'bg-blue-500',
    COMPLETED: 'bg-green-600',
    SAVED: 'bg-yellow-500',
  };

  const handleSelect = (status: updateStatusType | TaskUpdateStatus) => {
    onChange?.(status);
    setOpen(false); // ←確実に閉じる
  };

  // 外クリックで閉じる
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((prev) => !prev)}
        className={`rounded-lg min-w-[80px] h-6 px-2 text-white ${STATUS_COLORS[currentStatus]}`}
      >
        {STATUS_LABELS[currentStatus]}
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-40 bg-white border rounded shadow">
          {Object.entries(STATUS_LABELS).map(([status, label]) => (
            <button
              key={status}
              onClick={() => handleSelect(status as updateStatusType | TaskUpdateStatus)}
              className="block w-full text-left px-3 py-1 hover:bg-gray-100"
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
