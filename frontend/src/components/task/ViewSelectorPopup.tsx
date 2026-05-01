// src/components/task/ViewSelectorPopup.tsx

import type { CheckedState } from '@radix-ui/react-checkbox';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

import type { TaskUserAccessLevel } from '@/api/generated/taskProgressAPI.schemas';

import { SCOPE_LABELS } from '@/context/roleLabels';
import type { FilterAccessLevel } from '@/pages/TaskPage';
interface ViewSelectorPopupProps {
  viewMode: Record<FilterAccessLevel, boolean>;
  onChange: (newValue: Record<FilterAccessLevel, boolean>) => void;
}

export const ViewSelectorPopup = ({ viewMode, onChange }: ViewSelectorPopupProps) => {
  const handleOpenChange = (checked: CheckedState, key: FilterAccessLevel) => {
    const newViewMode = { ...viewMode, [key]: checked === true };
    onChange(newViewMode);
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">表示選択</Button>
      </PopoverTrigger>
      <PopoverContent className="w-48 p-2" align="start">
        {Object.entries(SCOPE_LABELS).map(([key, label]) => (
          <div key={key} className="flex items-center space-x-2">
            <Checkbox
              className="m-1"
              id={key}
              checked={viewMode[key as TaskUserAccessLevel]}
              onCheckedChange={(checked) => {
                handleOpenChange(checked, key as TaskUserAccessLevel);
              }}
            />
            <Label htmlFor={key}>{label}</Label>
          </div>
        ))}{' '}
        <div className="border-t my-2" />
        <div key="ASSIGNED" className="flex items-center space-x-2">
          <Checkbox
            className="m-1"
            id="ASSIGNED"
            checked={viewMode['ASSIGNED']}
            onCheckedChange={(checked) => {
              handleOpenChange(checked, 'ASSIGNED');
            }}
          />
          <Label htmlFor="ASSIGNED">担当者</Label>
        </div>
      </PopoverContent>
    </Popover>
  );
};
