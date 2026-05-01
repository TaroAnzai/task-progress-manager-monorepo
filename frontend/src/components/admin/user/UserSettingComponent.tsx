import { useMemo, useRef, useState } from 'react';

import { Check, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

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

import { usePutUsersUserId } from '@/api/generated/taskProgressAPI';
import type { User } from '@/api/generated/taskProgressAPI.schemas';

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
interface UserSettingComponentProps {
  user: User;
  className?: string;
  refetchUser: () => void;
}

export const UserSettingComponent = ({
  user,
  className,
  refetchUser,
}: UserSettingComponentProps) => {
  const [newName, setNewName] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [password2, setPassword2] = useState('');
  const nameFromRef = useRef<HTMLFormElement | null>(null);
  const pwFromRef = useRef<HTMLFormElement | null>(null);
  const strength = useMemo(() => calcStrength(password), [password]);
  const canSubmit = password.length >= 8 && password === password2;
  const { mutate: putUser, isPending } = usePutUsersUserId({
    mutation: {
      onSuccess: (_data, val) => {
        if ('name' in val.data) {
          toast.success('ユーザー名を変更しました');
          refetchUser();
          nameFromRef.current?.reset();
          setNewName('');
        }
        if ('password' in val.data) {
          toast.success('パスワードを変更しました');
          pwFromRef.current?.reset();
          setPassword('');
          setPassword2('');
        }
      },
      onError: (err) => {
        console.error(err);
        toast.error('変更に失敗しました');
      },
    },
  });

  const onSubmitPW = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      password: password,
    };
    putUser({ userId: user.id, data: payload });
  };
  const onSubmitName = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: newName,
    };
    putUser({ userId: user.id, data: payload });
  };
  return (
    <div className="flex justify-center space-x-4 p-4 border rounded bg-white shadow w-full">
      <Card className={`flex flex-col h-full p-4 ${className ?? ''}`}>
        <CardHeader>
          <CardTitle>ユーザー名変更</CardTitle>
          <CardDescription>ユーザー名を変更します。</CardDescription>
        </CardHeader>
        <CardContent>
          <form ref={nameFromRef} id="nameFrom" onSubmit={onSubmitName}>
            <div className="space-y-2">
              <Label htmlFor="newName">ユーザー名</Label>
              <Input
                id="newName"
                className="w-96"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={user.name}
              />
            </div>
          </form>
        </CardContent>
        <CardFooter className="mt-auto">
          <Button className="w-full" type="submit" form="nameFrom">
            変更
          </Button>
        </CardFooter>
      </Card>
      <Card className={`p-4  ${className ?? ''}`}>
        <CardHeader>
          <CardTitle>パスワード変更</CardTitle>
          <CardDescription>パスワードの変更をします。</CardDescription>
        </CardHeader>
        <CardContent>
          <form ref={pwFromRef} id="pwForm" onSubmit={onSubmitPW} className="">
            <div className="space-y-2">
              <Label htmlFor="password">新しいパスワード</Label>
              <div className="relative">
                <Input
                  className="w-96"
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
                <Check className={`w-3 h-3 ${/[0-9]/.test(password) ? 'text-emerald-600' : ''}`} />
                数字を含む
              </li>
              <li className="flex items-center gap-2">
                <Check
                  className={`w-3 h-3 ${/[A-Za-z]/.test(password) ? 'text-emerald-600' : ''}`}
                />
                英字を含む
              </li>
            </ul>
          </form>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" form="pwForm" className="w-full" disabled={!canSubmit || isPending}>
            {isPending ? '更新中...' : 'パスワードを更新する'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
