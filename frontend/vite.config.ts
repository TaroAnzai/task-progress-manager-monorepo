import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  const isDev = command === 'serve'; // npm run dev の場合

  const serverConfig = {
    host: '0.0.0.0',
    port: 5173,
  };


  return {
    plugins: [react()],
    base: isDev? '/' : '/progress-dev/',
    server: {
      ...serverConfig,
      proxy: {
        "/api": {
          target: "http://localhost:5000",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          secure: false,
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  };
});
