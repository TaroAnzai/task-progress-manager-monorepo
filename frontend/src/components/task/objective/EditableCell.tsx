// src/components/task/objective/EditableCell.tsx
import { useEffect, useState } from 'react';

import { Textarea } from '@/components/ui/textarea';

type EditableCellProps = {
  value: string;
  onSave: (newValue: string) => void;
  className?: string;
  disabled?: boolean;
};

export const EditableCell = ({ value, onSave, className, disabled }: EditableCellProps) => {
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState(value);

  useEffect(() => {
    setInputValue(value);
  }, [value]);
  const finishEditing = () => {
    setEditing(false);
    // 表示は常に親のvalue基準に戻す（親が成功なら後で新値に変わる）
    setInputValue(value);
  };
  const handleSave = () => {
    if (inputValue !== value) {
      onSave(inputValue);
    }
    finishEditing();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSave();
    } else if (e.key === 'Escape') {
      setEditing(false);
      setInputValue(value); // 元に戻す
    }
  };

  return editing ? (
    <Textarea
      value={inputValue}
      onChange={(e) => setInputValue(e.target.value)}
      onBlur={handleSave}
      onKeyDown={handleKeyDown}
      className="min-h-[40px] resize-none overflow-hidden" // h-[40px]を削除
      autoFocus
      rows={1}
      style={{
        height: 'auto',
        minHeight: '40px',
      }}
      ref={(textarea) => {
        if (textarea) {
          textarea.style.height = 'auto';
          textarea.style.height = textarea.scrollHeight + 'px';
        }
      }}
    />
  ) : disabled ? (
    <div
      onClick={() => setEditing(false)}
      className={`text-left w-full min-h-[1.5rem] ${className} whitespace-pre-wrap`}
    >
      {value || '+'}
    </div>
  ) : (
    <div
      onClick={() => setEditing(true)}
      className={`cursor-pointer text-left w-full min-h-[1.5rem] ${className} whitespace-pre-wrap`}
    >
      {value || '+'}
    </div>
  );
};
