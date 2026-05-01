import { useEffect, useState } from 'react';

import { isAxiosError } from 'axios';
import type { ReactNode } from 'react';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

import { extractErrorMessage } from '@/utils/errorHandler';

import { AlertDialogContext, type DialogOptions } from './AlertDialogContextBase';
export const AlertDialogProvider = ({ children }: { children: ReactNode }) => {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('確認');
  const [description, setDescription] = useState('');
  const [descriptionNode, setDescriptionNode] = useState<ReactNode>(null);
  const [onConfirm, setOnConfirm] = useState<() => void>(() => () => {});
  const [onCancel, setOnCancel] = useState<() => void>(() => {});
  const [confirmText, setConfirmText] = useState('OK');
  const [cancelText, setCancelText] = useState('キャンセル');
  const [showCancel, setShowCancel] = useState(true);

  const openAlertDialog = ({
    title = '確認',
    description = '',
    descriptionNode = null,
    onConfirm,
    onCancel,
    confirmText = 'OK',
    cancelText = 'キャンセル',
    showCancel = true,
  }: DialogOptions) => {
    setTitle(title);
    if (isAxiosError(description)) {
      setDescription(extractErrorMessage(description));
    } else if (typeof description === 'string') {
      setDescription(description);
    } else {
      setDescription('Unknown error');
    }
    setDescriptionNode(descriptionNode);
    setOnConfirm(() => () => {
      onConfirm?.();
      setOpen(false);
    });
    setOnCancel(() => () => {
      onCancel?.();
      setOpen(false);
    });
    setConfirmText(confirmText);
    setCancelText(cancelText);
    setShowCancel(showCancel);
    setOpen(true);
  };

  useEffect(() => {
    if (open && document.activeElement && document.activeElement !== document.body) {
      (document.activeElement as HTMLElement).blur();
    }
  }, [open]);

  return (
    <AlertDialogContext.Provider value={{ openAlertDialog }}>
      {children}
      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{title}</AlertDialogTitle>
            {description && (
              <AlertDialogDescription className="whitespace-pre-wrap">
                {description}
              </AlertDialogDescription>
            )}
            {descriptionNode}
          </AlertDialogHeader>
          <AlertDialogFooter>
            {showCancel && <AlertDialogCancel onClick={onCancel}>{cancelText}</AlertDialogCancel>}
            <AlertDialogAction onClick={onConfirm}>{confirmText}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AlertDialogContext.Provider>
  );
};
