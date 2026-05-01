import { Card, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import type { ObjectiveReminderSettingListOutput } from '@/api/generated/taskProgressAPI.schemas';

import { REMINDER_CONDITION_LABELS, REMINDER_FREQUENCY_LABELS } from '@/context/reminderLabels';
interface RemainderSettingModalProps {
  isLoading: boolean;
  reminderSettings: ObjectiveReminderSettingListOutput | undefined;
  onClick: (id: number) => void;
}
export const ReminderTable = ({ reminderSettings, onClick }: RemainderSettingModalProps) => {
  if (!reminderSettings) return <div>No reminder settings found.</div>;
  return (
    <Card className="mr-4 p-4">
      <CardTitle>設定一覧</CardTitle>
      <Table className="mt-4">
        <TableHeader>
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>条件</TableHead>
            <TableHead>経過日数</TableHead>
            <TableHead>頻度</TableHead>
            <TableHead>間隔</TableHead>
            <TableHead>送信時刻</TableHead>
            <TableHead>有効</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reminderSettings.items.map((r) => (
            <TableRow key={r.id} onClick={() => onClick(r.id)}>
              <TableCell>{r.id}</TableCell>
              <TableCell>{REMINDER_CONDITION_LABELS[r.condition_type]}</TableCell>
              <TableCell>{r.threshold_days}</TableCell>
              <TableCell>{REMINDER_FREQUENCY_LABELS[r.frequency_type]}</TableCell>
              <TableCell>{r.interval_days}</TableCell>
              <TableCell>{r.send_time_local}</TableCell>
              <TableCell>{r.is_active ? 'Yes' : 'No'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
};
