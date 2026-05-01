// eslint.config.js (Flat Config)
import js from '@eslint/js';
import { globalIgnores } from 'eslint/config';
import prettierConfig from 'eslint-config-prettier'; // ← 重複を解消しこれだけに統一
import eslintPluginImport from 'eslint-plugin-import';
import prettierPlugin from 'eslint-plugin-prettier';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config([
  // グローバル無視
  globalIgnores(['dist']),
  {
    ignores: ['src/api/generated/**', 'src/components/ui/**', 'src/lib/**'],
  },

  // TypeScript/React ファイルに適用するメイン設定
  {
    files: ['**/*.{ts,tsx}'],

    // 公式推奨に基づくプリセットの合成
    extends: [
      js.configs.recommended, // ESLint 本体の推奨
      ...tseslint.configs.recommended, // typescript-eslint 推奨（Flat Config）
      // react-hooks: v6 以降は recommended を使用。v5.2.0 系なら ['recommended-latest'] を使用
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite, // Vite + React Refresh
      prettierConfig, // Prettier 競合ルールを無効化
    ],

    // パーサ/グローバル
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },

    // プラグイン登録
    plugins: {
      import: eslintPluginImport,
      'simple-import-sort': simpleImportSort,
    },

    // ルール
    rules: {
      // import 並び替え/方針
      'import/order': 'off',
      'simple-import-sort/imports': [
        'warn',
        {
          groups: [
            // React
            ['^react$'],
            ['^type:react$'],

            // 外部ライブラリ
            ['^@?\\w'],
            ['^type:@?\\w'],

            // shadcn/ui（外部の次）
            ['^@/components/ui(/.*|$)'],
            ['^type:@/components/ui(/.*|$)'],

            // Orval 生成物
            ['^@/api/generated(/.*|$)'],
            ['^type:@/api/generated(/.*|$)'],

            // 内部 - フック
            ['^@/hooks(/.*|$)'],
            ['^type:@/hooks(/.*|$)'],

            // 内部 - コンポーネント（shadcn 以外）
            ['^@/components(/.*|$)'],
            ['^type:@/components(/.*|$)'],

            // 内部 - ユーティリティ / 定数
            ['^@/utils(/.*|$)', '^@/constants(/.*|$)'],
            ['^type:@/utils(/.*|$)', '^type:@/constants(/.*|$)'],

            // 残りの内部
            ['^@/'],
            ['^type:@/'],

            // 親相対
            ['^\\.\\.(?!/?$)', '^\\.\\./?$'],
            ['^type:^\\.\\.(?!/?$)', '^type:^\\.\\./?$'],

            // 同階層 & index
            ['^\\./(?!/?$)', '^\\.(?!/?$)', '^\\./?$'],
            ['^type:^\\./(?!/?$)', '^type:^\\.(?!/?$)', '^type:^\\./?$'],
          ],
        },
      ],
      'simple-import-sort/exports': 'warn',
      'import/prefer-default-export': 'off',
      'import/no-default-export': 'warn',
    },
  },

  // コーディングスタイルの微調整（共通）
  {
    rules: {
      'func-style': ['warn', 'expression', { allowArrowFunctions: true }],
      'prefer-arrow-callback': 'warn',
      'arrow-body-style': ['warn', 'as-needed'],
    },
  },

  // ページ配下は default export を許可
  {
    files: ['src/pages/**/*.{ts,tsx}', 'src/*.{ts,tsx}'],
    rules: {
      'import/no-default-export': 'off',
    },
  },

  // UI配下は React Refresh の制限を緩める
  {
    files: ['src/components/ui/**/*.tsx'],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
]);
