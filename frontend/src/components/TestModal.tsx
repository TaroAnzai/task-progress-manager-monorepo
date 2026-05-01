import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { DraggableRow, DraggableTable, DraggableTableBody } from "@/components/DraggableTable";
interface TestModalProps {
  open: boolean;
  onClose: () => void;
}
type Item = { id: number; name: string };
export const TestModal = ({ open, onClose }: TestModalProps) => {
  //const { tasks } = useTasks();

  const [items, setItems] = useState<Item[]>([
    { id: 1, name: "田中" },
    { id: 2, name: "佐藤" },
    { id: 3, name: "鈴木" },
  ]);

  const handleRender = (items: Item[]) => {
    console.log("render", items);
    setItems(items);
  }

  return (
    <Dialog open={open} onOpenChange={onClose} >
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col" >
        <DialogHeader className="flex-shrink-0" >
          <DialogTitle>TEST用のダイヤログ</DialogTitle>
          < DialogDescription > オリジナルDnDテスト</DialogDescription>
        </DialogHeader>
        <DraggableTable
          className=""
          items={items}
          getId={(item) => item.id}
          onReorder={handleRender}
          useGrabHandle={true}
        >
          <TableHeader className="sticky top-0 z-10 bg-white">
            <TableRow>
              <TableHead className="px-4 py-2">id</TableHead>
              <TableHead className="px-4 py-2">名前</TableHead>
            </TableRow>
          </TableHeader>
          <DraggableTableBody>
            {items.map((item) => (
              <DraggableRow key={item.id} id={item.id}>
                <td className="border px-4 py-2">{item.id}</td>
                <td className="border px-4 py-2">{item.name}</td>
              </DraggableRow>
            ))}
          </DraggableTableBody>
        </DraggableTable>
        <DialogFooter>
          <Button onClick={onClose}>閉じる</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog >
  )

};
