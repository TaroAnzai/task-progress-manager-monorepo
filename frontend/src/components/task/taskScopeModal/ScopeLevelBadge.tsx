import clsx from "clsx";
import { X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const ScopeLevelBadge = <T extends string,>({
  text,
  value,
  options,
  editable = false,
  onChange,
  onRemove,
  color = "gray",
  className,
}: {
  text: string;
  value: T;
  options: readonly { value: T; label: string }[];
  editable?: boolean;
  onChange?: (val: T) => void;
  onRemove?: () => void;
  color?: "blue" | "green" | "gray";
  className?: string;
}) => {
  const baseColor =
    color === "blue"
      ? "bg-blue-100 text-blue-800"
      : color === "green"
      ? "bg-green-100 text-green-800"
      : "bg-gray-100 text-gray-800";

  const TriggerButton = (
    <button
      type="button"
      className="flex items-center gap-2 pl-2 pr-4 py-1"
      // ボタン内は普通にトリガーとして反応
    >
      <span className="truncate max-w-[12rem]">{text}</span>
      <span className="rounded bg-white/70 px-1 text-xs">{value}</span>
    </button>
  );

  return (
    <Badge
      className={clsx(
        "relative inline-flex items-center pr-5", // ← 右に余白確保
        baseColor,
        className
      )}
    >
      {editable ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>{TriggerButton}</DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuRadioGroup
              value={value as string}
              onValueChange={(v) => onChange?.(v as T)}
            >
              {options.map((opt) => (
                <DropdownMenuRadioItem key={opt.value} value={opt.value as string}>
                  {opt.label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <div className="flex items-center gap-2 pl-2 pr-4 py-1">
          <span className="truncate max-w-[12rem]">{text}</span>
          <span className="rounded bg-white/70 px-1 text-xs">{value}</span>
        </div>
      )}

      {/* X はトリガーの外に配置（上に被せる） */}
      {onRemove && (
        <button
          type="button"
          aria-label="remove"
          className="absolute right-1 top-1/2 -translate-y-1/2 z-10 rounded p-0.5 hover:bg-black/10"
          onPointerDown={(e) => {
            // Radixのpointerdownトリガーを阻止
            e.preventDefault();
            e.stopPropagation();
          }}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onRemove();
          }}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </Badge>
  );
};
