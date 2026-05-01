import { useState } from 'react';

import { Eye, EyeOff } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';

import type { Login } from '@/api/generated/taskProgressAPI.schemas';
import { usePostSessions } from '@/api/generated/taskProgressAPI.ts';

import { extractErrorMessage } from '@/utils/errorHandler.ts';

import { useAlertDialog } from '@/context/useAlertDialog';
import { useUser } from '@/context/useUser';

// 定数の定義
const MESSAGES = {
  LOGIN_SUCCESS: 'ログイン成功',
  LOGIN_FAILED: 'ログイン失敗',
  LOGIN_TITLE: 'ログイン',
  EMAIL_LABEL: 'メールアドレス',
  PASSWORD_LABEL: 'パスワード',
  LOGIN_BUTTON: 'ログイン',
  LOGIN_LOADING: 'ログイン中...',
} as const;

const ROUTES = {
  DEFAULT: '/',
} as const;

// カスタムフック: ログイン処理の分離
const useLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from || ROUTES.DEFAULT;
  const { openAlertDialog } = useAlertDialog();
  const { refetchUser } = useUser();

  const mutation = usePostSessions({
    mutation: {
      onSuccess: async () => {
        await refetchUser();
        navigate(from, { replace: true });
      },
      onError: (error) => {
        const errorMessage = extractErrorMessage(error);
        openAlertDialog({
          title: 'エラー',
          description: `${MESSAGES.LOGIN_FAILED}: ${errorMessage}`,
          confirmText: '閉じる',
          showCancel: false,
        });
      },
    },
  });

  return {
    login: mutation.mutate,
    isLoading: mutation.isPending,
    from,
  };
};

// カスタムフック: フォーム状態管理の分離
const useLoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const resetForm = () => {
    setEmail('');
    setPassword('');
  };

  const getFormData = (): Login => ({
    email: email.trim(),
    password,
  });

  const isFormValid = () => email.trim() !== '' && password !== '';

  return {
    email,
    setEmail,
    password,
    setPassword,
    resetForm,
    getFormData,
    isFormValid,
  };
};

// UI コンポーネント: 入力フィールド
interface InputFieldProps {
  label: string;
  type: 'email' | 'password';
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}

const InputField = ({ label, type, value, onChange, required = false }: InputFieldProps) => {
  const [show, setShow] = useState(false);
  return (
    <div>
      <label
        htmlFor={type === 'password' ? (show ? 'text' : 'password') : type}
        className="block text-sm font-medium text-gray-700"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={type === 'password' ? (show ? 'text' : 'password') : type}
          name={type === 'password' ? (show ? 'text' : 'password') : type}
          type={type === 'password' ? (show ? 'text' : 'password') : type}
          autoComplete={type === 'password' ? 'current-password' : 'username'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring focus:ring-blue-200 focus:border-blue-400"
          required={required}
        />
        {type === 'password' && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-2 top-1/2 -translate-y-1/2"
            onClick={() => setShow((v) => !v)}
            aria-label={show ? 'パスワードを隠す' : 'パスワードを表示'}
          >
            {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </Button>
        )}
      </div>
    </div>
  );
};

// UI コンポーネント: ログインボタン
interface LoginButtonProps {
  isLoading: boolean;
  isDisabled: boolean;
}

const LoginButton = ({ isLoading, isDisabled }: LoginButtonProps) => (
  <Button
    type="submit"
    className="w-full py-2  transition disabled:opacity-50 disabled:cursor-not-allowed"
    disabled={isDisabled}
  >
    {isLoading ? MESSAGES.LOGIN_LOADING : MESSAGES.LOGIN_BUTTON}
  </Button>
);

// メインコンポーネント
export default function LoginPage() {
  const { login, isLoading } = useLogin();
  const { email, setEmail, password, setPassword, getFormData, isFormValid } = useLoginForm();

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!isFormValid()) {
      alert('メールアドレスとパスワードを入力してください');
      return;
    }

    const loginData = getFormData();
    login({ data: loginData });
  };

  return (
    <div className="flex flex-col justify-center items-center h-screen bg-gray-100">
      <div className="bg-white shadow-lg rounded-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6 text-center">{MESSAGES.LOGIN_TITLE}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            label={MESSAGES.EMAIL_LABEL}
            type="email"
            value={email}
            onChange={setEmail}
            required
          />

          <InputField
            label={MESSAGES.PASSWORD_LABEL}
            type="password"
            value={password}
            onChange={setPassword}
            required
          />

          <LoginButton isLoading={isLoading} isDisabled={isLoading || !isFormValid()} />
        </form>
        <div className="flex flex-col items-end mt-4">
          <div className="flex flex-col">
            <a href="/signup" className=" hover:underline ml-2">
              新規登録
            </a>
          </div>
          <div>
            <a href="/reset" className=" hover:underline ml-2">
              パスワードを忘れた場合
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
