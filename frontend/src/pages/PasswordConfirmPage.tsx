// src/pages/ResetPasswordPage.tsx
import * as React from 'react';
import { useMemo, useState } from 'react';

import { AlertCircle, Check, Eye, EyeOff, Lock } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';

import { usePostAuthPasswordResetConfirm } from '@/api/generated/taskProgressAPI';

import { useAlertDialog } from '@/context/useAlertDialog';
const calcStrength = (pw: string) => {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  // 0..5 -> 0..100
  return Math.min(100, Math.round((score / 5) * 100));
};

export default function PasswordConfirmPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = (params.get('token') || '').trim();
  const { openAlertDialog } = useAlertDialog();

  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [show, setShow] = useState(false);

  const strength = useMemo(() => calcStrength(password), [password]);
  const canSubmit = token.length > 0 && password.length >= 8 && password === password2;
  const { mutate: postPassword, isPending: isPostPasswordPending } =
    usePostAuthPasswordResetConfirm({
      mutation: {
        onSuccess: () => {
          toast.success('新しいパスワードを設定しました');
          navigate('/login');
        },
        onError: (err) => {
          console.error(err);
          openAlertDialog({
            title: 'Error',
            description: err,
            confirmText: '閉じる',
            showCancel: false,
          });
        },
      },
    });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit || isPostPasswordPending) return;
    postPassword({ data: { token: token, new_password: password } });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lock className="w-5 h-5 text-primary" />
            <CardTitle>パスワードの再設定</CardTitle>
          </div>
          <CardDescription>
            受信したメール内のリンクから遷移しています。新しいパスワードを入力してください。
          </CardDescription>
        </CardHeader>

        <CardContent>
          {token ? (
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">新しいパスワード</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={show ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="8文字以上を推奨"
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                    onClick={() => setShow((v) => !v)}
                    aria-label={show ? 'パスワードを隠す' : 'パスワードを表示'}
                  >
                    {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <div className="space-y-1">
                  <Progress value={strength} />
                  <p className="text-xs text-muted-foreground">
                    強度: {strength >= 80 ? '強い' : strength >= 50 ? '普通' : '弱い'}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password2">新しいパスワード（確認）</Label>
                <Input
                  id="password2"
                  type="password"
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                  required
                />
                {password2.length > 0 && password !== password2 && (
                  <p className="text-xs text-red-500">パスワードが一致しません</p>
                )}
              </div>

              <ul className="text-xs text-muted-foreground space-y-1">
                <li className="flex items-center gap-2">
                  <Check className={`w-3 h-3 ${password.length >= 8 ? 'text-emerald-600' : ''}`} />
                  8文字以上
                </li>
                <li className="flex items-center gap-2">
                  <Check
                    className={`w-3 h-3 ${/[0-9]/.test(password) ? 'text-emerald-600' : ''}`}
                  />
                  数字を含む
                </li>
                <li className="flex items-center gap-2">
                  <Check
                    className={`w-3 h-3 ${/[A-Za-z]/.test(password) ? 'text-emerald-600' : ''}`}
                  />
                  英字を含む
                </li>
              </ul>

              <Button
                type="submit"
                className="w-full"
                disabled={!canSubmit || isPostPasswordPending}
              >
                {isPostPasswordPending ? '更新中...' : 'パスワードを更新する'}
              </Button>
            </form>
          ) : (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>リンクが無効です</AlertTitle>
              <AlertDescription>
                URLにトークンが見つかりませんでした。お手数ですが、もう一度パスワード再設定メールの送信をお試しください。
              </AlertDescription>
            </Alert>
          )}
        </CardContent>

        <CardFooter className="flex justify-between">
          <Button variant="ghost" onClick={() => navigate('/login')}>
            ログインへ戻る
          </Button>
          <Button variant="outline" onClick={() => navigate('/forgot-password')}>
            再設定メールを送る
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
