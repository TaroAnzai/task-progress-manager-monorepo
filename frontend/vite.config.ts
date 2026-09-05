import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  const isDev = command === 'serve';

  return {
    plugins: [react()],
    envDir: '..',
    base: isDev ? '/' : '/progress/',
    server: {
      host: '0.0.0.0',
      port: 5174,
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  };
});
