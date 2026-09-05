// src/App.tsx

import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';

import { Header } from '@/components/layout/Header';

import LoginPage from '@/pages/LoginPage'; // ✅ ログインページを追加
import PasswordConfirmPage from '@/pages/PasswordConfirmPage';
import PasswordResetRequestPage from '@/pages/PasswordResetPage';
import ProgressAdminPage from '@/pages/ProgressAdminPage.tsx';
import SignupPage from '@/pages/SignupPage';
import TaskPage from '@/pages/TaskPage';

import './index.css'; // ✅ Tailwindを有効にする

export default function App() {
  const basename = import.meta.env.BASE_URL.replace(/\/$/, '');
  return (
    <Router basename={basename}>
      <div className="flex h-screen flex-col overflow-hidden bg-gray-100">
        <Header />
        <main className="min-h-0 flex-1">
          <Routes>
            <Route path="/" element={<TaskPage />} />

            <Route path="/login" element={<LoginPage />} />
            <Route path="/admin" element={<ProgressAdminPage />} />
            <Route path="/reset" element={<PasswordResetRequestPage />} />
            <Route path="/reset-password" element={<PasswordConfirmPage />} />
            <Route path="/signup" element={<SignupPage />} />
          </Routes>
          <Toaster richColors position="top-center" />
        </main>
      </div>
    </Router>
  );
}
