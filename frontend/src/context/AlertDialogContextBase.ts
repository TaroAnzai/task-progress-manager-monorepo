import { createContext } from "react";

import type { ReactNode } from "react";

export type DialogOptions = {
  title?: string;
  description?: unknown;
  descriptionNode?: ReactNode;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  showCancel?: boolean;
};

export type DialogContextType = {
  openAlertDialog: (options: DialogOptions) => void;
};

export const AlertDialogContext = createContext<DialogContextType | undefined>(undefined);
