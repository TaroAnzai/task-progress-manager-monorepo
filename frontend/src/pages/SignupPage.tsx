import { Building2, Mail, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

export default function SignupPage() {
  return (
    <div className="min-h-[calc(100vh-120px)] flex items-center justify-center p-4">
      <Card className="w-full max-w-xl shadow-xl">
        <CardHeader className="space-y-2">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <UserPlus className="h-4 w-4" />
            <span>アカウントの新規作成</span>
          </div>
          <CardTitle>新規登録について</CardTitle>
          <CardDescription>
            現在、このシステムではユーザーによる{' '}
            <span className="font-medium">自動登録は行っていません</span>
            。以下の案内に沿ってご連絡ください。
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5 text-sm leading-6">
          <div className="flex items-start gap-3">
            <Building2 className="h-5 w-5 mt-0.5 text-muted-foreground" />
            <p>
              会社・組織の <span className="font-medium">新規ユーザー登録</span>{' '}
              を希望される場合は、<span className="font-medium">所属先の管理者</span>
              に連絡してください。
            </p>
          </div>

          <div className="flex items-start gap-3">
            <Mail className="h-5 w-5 mt-0.5 text-muted-foreground" />
            <p>
              新規に <span className="font-medium">会社登録</span> を希望される場合は、
              <a href="mailto:support@anzai-home.com" className="underline underline-offset-4 ml-1">
                support@anzai-home.com
              </a>
              にご連絡ください。
            </p>
          </div>

          <div className="rounded-md border bg-muted/40 p-3 text-muted-foreground">
            登録手続き完了後、ログイン用メールが送信されます。メールが届かない場合は迷惑メールフォルダをご確認ください。
          </div>
        </CardContent>

        <CardFooter className="flex justify-end gap-2">
          <Button asChild variant="secondary">
            <Link to="/login">ログインページへ</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

/*
使用メモ:

1) ルーティング登録例
// src/App.tsx
// import SignupPage from '@/pages/SignupPage'
// <Route path="/signup" element={<SignupPage />} />

2) ログインページ等からの導線
// <Link to="/signup" className="text-sm underline text-muted-foreground">新規登録</Link>
*/
