// src/App.tsx

import { lazy, Suspense } from 'react';

import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';

import { Header } from '@/components/layout/Header';

import './index.css'; // ✅ Tailwindを有効にする

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const PasswordConfirmPage = lazy(() => import('@/pages/PasswordConfirmPage'));
const PasswordResetRequestPage = lazy(() => import('@/pages/PasswordResetPage'));
const ProgressAdminPage = lazy(() => import('@/pages/ProgressAdminPage'));
const SignupPage = lazy(() => import('@/pages/SignupPage'));
const TaskPage = lazy(() => import('@/pages/TaskPage'));

const PageLoadingFallback = () => (
  <div
    className="flex h-full items-center justify-center"
    role="status"
    aria-label="ページを読み込み中"
  >
    <span className="text-sm text-gray-500">読み込み中...</span>
  </div>
);

export default function App() {
  const basename = import.meta.env.BASE_URL.replace(/\/$/, '');
  return (
    <Router basename={basename}>
      <div className="flex h-screen flex-col overflow-hidden bg-gray-100">
        <Header />
        <main className="min-h-0 flex-1">
          <Suspense fallback={<PageLoadingFallback />}>
            <Routes>
              <Route path="/" element={<TaskPage />} />

              <Route path="/login" element={<LoginPage />} />
              <Route path="/admin" element={<ProgressAdminPage />} />
              <Route path="/reset" element={<PasswordResetRequestPage />} />
              <Route path="/reset-password" element={<PasswordConfirmPage />} />
              <Route path="/signup" element={<SignupPage />} />
            </Routes>
          </Suspense>
          <Toaster richColors position="top-center" />
        </main>
      </div>
    </Router>
  );
}
