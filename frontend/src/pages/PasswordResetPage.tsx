import { useState } from 'react';

import { Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Orval 生成フック & スキーマ
import { usePostAuthPasswordResetRequest } from '@/api/generated/taskProgressAPI';
import type { PasswordResetRequest } from '@/api/generated/taskProgressAPI.schemas';

export default function PasswordResetRequestPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const { mutate: requestReset, isPending } = usePostAuthPasswordResetRequest({
    mutation: {
      onSuccess: () => {
        toast.success('メールを送信しました。');
        setSent(true);
      },
      onError: () => {
        toast.error('Error');
      },
    },
  });

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    const payload: PasswordResetRequest = { email };
    requestReset({ data: payload });
  };

  return (
    <div className="min-h-[calc(100vh-120px)] flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader>
          <CardTitle>パスワード再設定</CardTitle>
          <CardDescription>
            ご登録のメールアドレス宛に、パスワード再設定用のリンクを送信します。
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                入力いただいたメールアドレス宛に、パスワード再設定のご案内をお送りしました。メールに記載の手順に従って操作してください。
              </p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>メールが届かない場合:</span>
                <ul className="list-disc list-inside">
                  <li>迷惑メールフォルダをご確認ください</li>
                  <li>数分待って再度お試しください</li>
                </ul>
              </div>
              <div className="flex gap-2">
                <Button asChild variant="secondary" className="w-full">
                  <Link to="/login">ログインへ戻る</Link>
                </Button>
                <Button variant="outline" className="w-full" onClick={() => setSent(false)}>
                  別のメールで試す
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email">メールアドレス</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    送信中...
                  </span>
                ) : (
                  '再設定メールを送信'
                )}
              </Button>

              <div className="text-center text-sm text-muted-foreground">
                <span>アカウントをお持ちでない方は </span>
                <Link className="underline" to="/signup">
                  新規登録
                </Link>
                <span> へ</span>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
