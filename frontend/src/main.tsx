import React from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';

import App from './App.tsx';
import { AlertDialogProvider } from './context/AlertDialogProvider';
import { TaskProvider } from './context/TaskProvider';
import { UserProvider } from './context/UserProvider';

import './index.css';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <UserProvider>
        <AlertDialogProvider>
          <TaskProvider>
            <App />
          </TaskProvider>
        </AlertDialogProvider>
      </UserProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
