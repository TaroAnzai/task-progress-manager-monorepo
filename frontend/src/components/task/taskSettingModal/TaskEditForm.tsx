// src/components/task/taskSettingModal/TaskEditForm.tsx

import type { ChangeEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface TaskEditFormProps {
  formState: {
    title: string;
    description: string;
    due_date: string;
  };
  isEditable: boolean;
  onChange: (key: string, value: string) => void;
}

export const TaskEditForm = ({ formState, isEditable, onChange }: TaskEditFormProps) => {
  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    onChange(name, value);
  };

  return (
    <div className="space-y-4 py-2">
      <div>
        <Label htmlFor="title">タスク名</Label>
        <Input
          id="title"
          name="title"
          value={formState.title}
          onChange={handleInputChange}
          disabled={!isEditable}
        />
      </div>

      <div>
        <Label htmlFor="description">説明</Label>
        <Textarea
          id="description"
          name="description"
          value={formState.description}
          onChange={handleInputChange}
          disabled={!isEditable}
        />
      </div>

      <div>
        <Label htmlFor="due_date">締切日</Label>
        <Input
          id="due_date"
          name="due_date"
          type="date"
          value={formState.due_date || ""}
          onChange={handleInputChange}
          disabled={!isEditable}
        />
      </div>
    </div>
  );
};

