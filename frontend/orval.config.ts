import { config } from 'dotenv';

config({ path: '.env.production' });

export default {
  progressApi: {
    input: process.env.VITE_OPENAPI_URL,
    output: {
      mode: 'split',
      target: './src/api/generated/',
      client: 'react-query',
      clean: true,
      httpClient: 'axios',
      override: {
        mutator: {
          path: './src/api/axiosInstance.ts',
          name: 'customInstance',
        },
      },
    },
  },
};
