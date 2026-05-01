import { useContext } from "react";

import { AlertDialogContext, type DialogContextType } from "./AlertDialogContextBase";

export const useAlertDialog = (): DialogContextType => {
  const context = useContext(AlertDialogContext);
  if (!context) throw new Error("useAlertDialog must be used within an AlertDialogProvider");
  return context;
}

/* AXIOS ERROR 例
     const { openAlertDialog } = useAlertDialog();

      onError:(error) => {
        openAlertDialog({
          title: "Error",
          description: error,
          confirmText: "閉じる",
          showCancel: false,
        });
      }

*/




/*   const { openAlertDialog } = useAlertDialog();

    openAlertDialog({
      title: "削除の確認",
      description: "このデータを削除してもよろしいですか？",
      confirmText: "削除する",
      cancelText: "キャンセル",
      onConfirm: () => {
        console.log("削除処理を実行");
      },
      onCancel: () => {
        console.log("キャンセルされました");
      },
    });

    
    | 引数名           | 型            | 必須 | 説明                            |
| ------------- | ------------ | -- | ----------------------------- |
| `title`       | `string`     | ✔  | ダイアログの見出し                     |
| `description` | `string`     | ✖  | ダイアログ本文                       |
| `confirmText` | `string`     | ✖  | 確定ボタンのラベル（デフォルト: "OK"）        |
| `cancelText`  | `string`     | ✖  | キャンセルボタンのラベル（デフォルト: "キャンセル"）  |
| `showCancel`  | `boolean`    | ✖  | キャンセルボタンを表示するか（デフォルト: `true`） |
| `onConfirm`   | `() => void` | ✖  | 確定ボタン押下時の処理                   |
| `onCancel`    | `() => void` | ✖  | キャンセルボタン押下時の処理                | */
