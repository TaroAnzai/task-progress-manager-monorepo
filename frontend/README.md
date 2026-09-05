# Task Progress Manager

タスクの進捗を視覚的かつ効率的に管理できる、React ベースの Web アプリケーションです。

## 📌 概要

このアプリは、複数のタスクに対して進捗状況を記録・管理し、オブジェクティブ（目標）単位での可視化を可能にするツールです。  
既存のバックエンド（Flask API）と連携してデータを取得・更新します。

## 🚀 技術スタック

| 分類                      | 使用技術                             | 補足                                      |
| ----------------------- | -------------------------------- | --------------------------------------- |
| **Frontend**            | **React**                        | Viteを用いたSPA構成                           |
| **Build Tool**          | **Vite**                         | 高速ビルド・ホットリロード対応                         |
| **HTTP通信**              | **Axios**                        | 認証トークン付与や共通エラーハンドリングをカスタムインスタンスで管理      |
| **データフェッチング & キャッシュ管理** | **React Query**                  | サーバー状態管理、キャッシュ、自動リフェッチを担う               |
| **APIクライアント自動生成**       | **Orval**                        | OpenAPI仕様からReact Query Hooks & 型定義を自動生成 |
| **状態管理（ローカル）**          | **React Hooks**                  | useState, useEffectなどでUIローカル状態を管理       |
| **スタイリング**              | **Tailwind CSS** ＋ **shadcn/ui** | シンプルかつ拡張性の高いUI構築                        |
| **バックエンドAPI**           | **Flask**                        | 別リポジトリで運用                               |


## 🔗 API呼び出し方針

開発時の `VITE_API_BASE_URL` は `https://auth.local:5000` です。ブラウザは通常API・email/password login・OIDC loginのすべてへ直接接続し、Cookie送信のためAxiosの `withCredentials: true` を維持します。Viteの `/api` proxyは使用しません。


本アプリケーションでは、**Flask-Smorest が生成する OpenAPI 仕様**を利用し、
型安全かつメンテナンス性の高い API 呼び出しを実現しています。

### **方針概要**

* **OpenAPI仕様**：Flask-Smorestの `/openapi.json` を利用
* **コード生成**：[orval](https://orval.dev/) により **React Query Hooks** および TypeScript 型定義を自動生成
* **HTTPクライアント**：Axios（共通インスタンスを利用、認証ヘッダーやエラーハンドリングを一元化）
* **service層**：初期段階から導入し、API呼び出しロジックをUIから分離

---

## 🏗 **ディレクトリ構成（API関連）**

```
src/
├── api/
│   ├── generated/
│   │   ├── progressApi.ts        # Orval自動生成のReact Query Hooks
│   │   └── model/                # Orval自動生成の型定義
│   ├── service/                  # サービス層（UI用の型変換・ラップ関数）
│   │   ├── taskService.ts
│   │   ├── authService.ts
│   │   └── ...
│   └── axiosInstance.ts          # Axiosカスタムインスタンス
├── components/                    # shadcnベースのUIコンポーネント
├── pages/                         # 各ページ単位のコンポーネント
├── hooks/                         # カスタムフック（必要に応じて）
├── App.tsx
└── main.tsx
```

---

## ⚡ **開発フロー**

### **1. バックエンド更新時（型定義・Hooksの更新）**

以下を実行するだけで、最新のAPI仕様が反映されます。

```bash
npm run generate:api
```

* **処理内容**：

  1. `/openapi.json` をダウンロード
  2. orval により `src/api/generated/` を自動生成（Hooks & 型定義更新）

---

### **2. フロント実装時**

* **service層を通じて呼び出すのが基本方針です。**
  UI側は `useTasks()` のように呼ぶだけで、状態管理（ローディング、エラー、再取得）は自動化されています。

#### ✅ 例：タスク取得と更新

```tsx
// pages/TaskList.tsx
import { useTasks } from '@/api/service/taskService';

export const TaskList = () => {
  const { data: tasks, isLoading, error, updateTask } = useTasks();

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error loading tasks</p>;

  return (
    <ul>
      {tasks?.map((task) => (
        <li key={task.id}>
          {task.title}
          <button onClick={() => updateTask({ id: task.id, title: '更新済み' })}>
            更新
          </button>
        </li>
      ))}
    </ul>
  );
};
```

---

### **3. 将来拡張**

* **サーバー切替対応**：環境変数（`.env`）を切り替えるだけで対応可能
* **キャッシュ制御や楽観的UI更新が必要になった場合**：
  service層内の修正のみで対応可能（UI側は変更不要）

---

### **4. 環境変数（例）**

```
VITE_API_BASE_URL=https://api.anzai-home.com/progress
VITE_OPENAPI_URL=https://api.anzai-home.com/openapi.json
```

---

### **5. 利点まとめ**

* ✅ **型安全・メンテナンス性が高い**（OpenAPI→orval→自動生成）
* ✅ **状態管理の自動化**（React Query活用）
* ✅ **保守性向上**（service層にロジック集約）
* ✅ **将来の拡張・サーバー移行も容易**（環境変数とservice層で吸収）


## 🔧 セットアップ手順

```bash
# リポジトリをクローン
git clone https://github.com/your-username/task-progress-manager.git
cd task-progress-manager

# 依存パッケージをインストール
npm install

# 開発サーバーを起動
npm run dev
````

---

## 🔗 バックエンドAPIとの連携

このプロジェクトは、バックエンド（Flask API）との通信に以下の仕組みを採用しています。

### **API呼び出し構成**

* **OpenAPI仕様**: Flask-Smorestが自動生成する `/openapi.json` を利用
* **[orval](https://orval.dev/)**: OpenAPI仕様から **React Query Hooks** と **TypeScript型定義**を自動生成
* **Axios（カスタムインスタンス）**: 認証ヘッダーやエラーハンドリングを一元管理

### **メリット**

1. **型安全** – API型はバックエンドと常に同期
2. **開発効率向上** – 生成されたHooks（例：`useGetTasks()`）を直接利用可能
3. **状態管理自動化** – React Queryがローディング・キャッシュ・エラー管理を自動化
4. **簡単な保守** – バックエンドが更新された際は以下のコマンドを実行するだけ

```bash
npx orval
```

### **実装例**

```tsx
import { useGetTasks } from '@/api/progressApi';

const TaskList = () => {
  const { data: tasks, isLoading, error } = useGetTasks();

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error!</p>;

  return (
    <ul>
      {tasks?.map(task => (
        <li key={task.id}>{task.title}</li>
      ))}
    </ul>
  );
};
```

### **orval 設定ファイル例（`orval.config.ts`）**

```ts
export default {
  progressApi: {
    input: 'http://127.0.0.1:5001/doc/openapi.json',
    output: {
      target: './src/api/progressApi.ts',
      client: 'react-query',
      override: {
        mutator: {
          path: './src/api/customAxios.ts', // 認証などを付与する場合
          name: 'customInstance',
        },
      },
    },
  },
};
```


