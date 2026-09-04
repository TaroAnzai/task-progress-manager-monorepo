Task Progress Manager Monorepo

<!-- ヘッダー用のイメージは `images/` ディレクトリに配置できます（任意） -->

概要
Task Progress Manager は、タスクや目標の進捗を視覚的に管理し、組織の権限に応じた操作を提供するフルスタックアプリケーションです。フロントエンドは React/Vite による SPA として実装され、バックエンドは Flask‐Smorest を用いた REST API で構築されています。ユーザーはブラウザからタスクを作成・編集・閲覧し、API 経由で他システムとも連携できます。

このリポジトリは monorepo 形式でフロントエンドとバックエンドをまとめて管理します。バックエンドのみの単体利用やフロントエンドだけの開発も可能です。

主な機能
進捗管理 – タスクやオブジェクティブ（目標）の進捗率を記録し、グラフや一覧で可視化します。

REST API – Flask‐Smorest により OpenAPI 仕様の API を提供し、自動生成されたドキュメント (/swagger-ui) から操作できます
。

エクスポート機能 – タスクを Excel や YAML 形式でエクスポートでき、バックアップや他システムとの連携に活用できます
。

スケジュール処理 – APScheduler や Celery (任意) を使って定期バッチや非同期ジョブを実行できます
。

認可とロール – システム管理者、組織管理者、メンバーといった役割や、タスクごとの権限レベル（full/edit/view）を定義し、安全なアクセス制御を実現します
。

型安全なフロントエンド – Orval で OpenAPI から自動生成した React Query Hooks と TypeScript 型定義を利用し、型安全でメンテナンス性の高いクライアントを実現します
。

技術スタック
バックエンド
言語/フレームワーク: Python 3.10+, Flask 3.x, Flask‑Smorest

データベース: MySQL 8.x + SQLAlchemy 2.x

マイグレーション: Flask‑Migrate

ジョブ管理: APScheduler、Redis + Celery (任意)

その他ライブラリ: Pandas, OpenPyXL, PyYAML（エクスポート機能）

フロントエンド
フレームワーク: React + TypeScript、Vite

状態管理/データ取得: React Query

HTTP クライアント: Axios (共通インスタンスで認証・エラー処理を集約)

API クライアント生成: Orval – OpenAPI 仕様から Hooks と型定義を自動生成

スタイリング: Tailwind CSS、shadcn/ui

はじめに
前提条件
Python 3.10 以上と Node.js 18 以上がインストールされていること。

MySQL サーバー (または適切な DATABASE_URL で指定したデータベース)。

インストール
リポジトリをクローン

git clone https://github.com/your-name/task-progress-manager-monorepo.git
cd task-progress-manager-monorepo
バックエンドのセットアップ

cd backend
python -m venv venv
source venv/bin/activate # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# リポジトリルートに環境変数ファイルを作成

cd ..
cp .env.example .env

# .env を編集して DATABASE_URL や SECRET_KEY などを設定

# データベース初期化（初回のみ）

flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 開発サーバー起動

flask run # 本番環境では gunicorn を推奨
フロントエンドのセットアップ

cd ../frontend
npm install

# API 基底 URL と OpenAPI URL はリポジトリルートの .env に設定

# OpenAPI 仕様から API クライアントを生成

npm run generate:api

# フロントエンド開発サーバー起動

npm run dev
## 開発環境

環境固有値と秘密情報はリポジトリルートの `.env` だけで管理します。
`.env` はGit追跡対象外で、`.env.example` が設定項目の正本です。

Backend、DB、Redis、Celery、Mailhog などの backend 系サービスは Docker Compose で起動します。

```bash
cp .env.example .env
# .env に開発用の値を設定
docker compose config
docker compose up -d --build
docker compose ps
```

開発では `compose.yaml + compose.override.yaml + .env` が自動適用されます。
MySQL、Redis、Mailhogは開発用ポートをホストへ公開します。

Frontend は Docker Compose に含まれません。別のターミナルでホスト上から手動起動します。

```bash
cd frontend
npm install
npm run generate:api
npm run dev
```

`frontend/orval.config.ts` と Vite はリポジトリルートの `.env` を参照します。

## 本番デプロイ

Backend と Frontend の運用先は分離されています。

```text
backend VPS                 GitHub Actions
├─ backend                       │ npm ci / Orval / build
├─ db                            ▼
├─ redis                    frontend/dist
├─ celery_worker                 │ SCP
├─ celery_beat                   ▼
└─ db_init                  Frontend 配信サーバー
```

### Backend

本番サーバーに本番用の `.env` を配置し、必須値を設定してください。

```bash
compose=(docker compose -f compose.yaml -f compose.production.yaml)
"${compose[@]}" config --quiet
"${compose[@]}" up -d --build
```

本番では `compose.override.yaml` を指定しません。DBとRedisはホストへ公開されず、
Backend は reverse proxy 向けに `127.0.0.1` へ bind されます。Frontend はこの Compose 構成には含まれません。

### Frontend と GitHub Actions

`.github/workflows/backend.yml` は `backend/**`、`frontend/**`、Compose ファイル、または各 deployment workflow が変更されて
`main` へ push された場合に起動し、変更内容を判定します。Backend 関連ファイルが変更された場合は、
`backend` Environment の Variables と Secrets を使って Backend をデプロイします。Frontend のみの変更では
Backend deployment job をスキップします。

Backend workflow が正常終了すると、`workflow_run` により `.github/workflows/frontend.yml` が独立した workflow として起動します。
このため、Backend 関連の変更では Backend deployment の完了後に新しい OpenAPI endpoint を使って Orval と Frontend buildを実行し、
Frontend のみの変更でも不要な Backend deploymentを行わずにFrontendをデプロイします。Frontend workflow は常に
`frontend` Environment の Variables と Secrets を使用するため、同名の `SSH_KEY` や `SSH_HOST` が Backend と混在しません。
両方の workflow は `workflow_dispatch` による個別の手動実行にも対応します。

GitHub の Environments に `backend` と `frontend` を作成し、次の設定を登録します。
値はリポジトリへ保存しません。秘密情報である SSH private key だけを Secret とし、その他は Variables にします。

#### `backend` Environment

| 種類 | 名前 | 用途 |
| --- | --- | --- |
| Secret | `SSH_KEY` | backend VPS の SSH private key |
| Variable | `SSH_HOST` | backend VPS の SSH host |
| Variable | `SSH_USER` | backend VPS の SSH user |
| Variable | `SSH_PORT` | backend VPS の SSH port |

#### `frontend` Environment

| 種類 | 名前 | 用途 |
| --- | --- | --- |
| Secret | `SSH_KEY` | Frontend 配信サーバーの SSH private key |
| Variable | `SSH_HOST` | Frontend 配信サーバーの SSH host |
| Variable | `SSH_USER` | Frontend 配信サーバーの SSH user |
| Variable | `SSH_PORT` | Frontend 配信サーバーの SSH port |
| Variable | `FRONTEND_DEPLOY_PATH` | `dist` の内容を配置する公開ディレクトリ |
| Variable | `VITE_API_BASE_URL` | ブラウザから利用する本番 API base URL |
| Variable | `VITE_OPENAPI_URL` | Orval が取得する本番 OpenAPI JSON URL |

既存の Repository Secrets は Environment 設定への移行後に削除できます。少なくとも `SSH_HOST`、`SSH_USER`、`SSH_PORT` は
Secrets ではなく各 Environment の Variables に移し、`SSH_KEY` は各 Environment の Secret として登録します。

### 旧 Frontend コンテナの移行

新しい Frontend 配信サーバーへの deployment が成功したことを確認してから、一度だけ backend VPS 上の旧コンテナを削除します。
まず対象をラベルで確認し、表示された frontend コンテナだけを名前または ID で指定してください。

```bash
docker ps -a \
  --filter label=com.docker.compose.project=task-progress-docker \
  --filter label=com.docker.compose.service=frontend
docker rm -f task-progress-docker-frontend-1
```

Compose project 名やコンテナ名が異なる場合は、1つ目のコマンドに表示された名前を使用します。
DB volume を削除する `docker compose down -v` は使用しません。

主要な環境変数
バックエンドの config.py では多数の環境変数を読み込みます。最低限必要なものは以下です。

| 変数名 | 用途 |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy に渡す DB 接続文字列 |
| `SECRET_KEY` | セッションや CSRF token に使用する秘密鍵 |
| `FRONTEND_URL` | Backend が CORS や Frontend URL の生成に使用する URL |
| `FRONTEND_BASE_URL` | password reset link の生成に使用する Frontend URL |
| `CORS_ORIGINS` | アクセスを許可する domain のカンマ区切りリスト |
| `API_TITLE` / `API_VERSION` | OpenAPI document の title と version |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | 非同期 job 用の Redis URL |
| `SMTP_HOST` / `SMTP_USERNAME` / `SMTP_PASSWORD` | mail 送信に利用する SMTP server 情報 |
| `OIDC_ISSUER_URL` | CIH Realm の Issuer URL |
| `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` | Keycloak の confidential client 認証情報 |
| `OIDC_REDIRECT_URI` | Backend の `/sessions/oidc/callback` の完全URL |
| `OIDC_FRONTEND_REDIRECT_URL` | OIDCログイン成功後に戻るFrontend URL |
| `GOOGLE_API_KEY` / `GEMINI_MODEL` | Gemini API の設定 |

フロントエンドでは、以下の環境変数を .env に設定します:

| 変数名 | 用途 |
| --- | --- |
| `VITE_API_BASE_URL` | Backend API の base URL（開発時の既定例は `/api`） |
| `VITE_OPENAPI_URL` | OpenAPI JSON の URL（例: `http://localhost:5000/doc/openapi.json`） |

## Common Identity Hub側の設定

Keycloak Realm `anzai-home` に次のOIDC Clientを登録します。

| 設定 | 値 |
| --- | --- |
| Client ID | `task-progress-manager` |
| Client type | OpenID Connect / confidential（Client authentication有効） |
| Standard Flow | 有効 |
| PKCE method | `S256` |
| Valid Redirect URI（本番） | 本番Backendの `https://<backend-host>/sessions/oidc/callback` |
| Valid Redirect URI（開発） | `http://localhost:5000/sessions/oidc/callback` |
| Web Origin（本番） | 本番FrontendのOrigin |
| Web Origin（開発） | `http://localhost:5174` |

本番の `OIDC_ISSUER_URL` は `https://auth.anzai-home.com/realms/anzai-home` を設定します。
Client Secretの実値はリポジトリへ保存せず、本番サーバーの `.env` だけに設定してください。
Discovery、JWKS署名検証、state、nonce、Authorization Code Flow + PKCEはBackendが処理します。
FrontendへID TokenやAccess Tokenは渡しません。

プロジェクト構成
task-progress-manager-monorepo/
├── backend/ # Flask API (task progress 管理)
│ ├── app/ # モデル・ルート・サービス・スキーマ
│ ├── migrations/ # Alembic マイグレーション
│ ├── docs/ # 設計や権限仕様のドキュメント
│ ├── requirements.txt
│ └── run.py # アプリケーションのエントリポイント
├── frontend/ # React + Vite SPA
│ ├── src/ # コンポーネント、ページ、hooks 等
│ ├── public/ # 静的ファイル
│ ├── orval.config.ts # OpenAPI からクライアント生成する設定
│ └── README.md # フロントエンド固有のドキュメント
├── compose.yaml # 開発・本番の共通設定
├── compose.override.yaml # 開発専用差分
├── compose.production.yaml # 本番専用差分
├── .env.example # 環境変数テンプレート
└── README.md (このファイル)
使い方
ブラウザでフロントエンド (デフォルト http://localhost:5173 ) にアクセスします。

ログイン後、タスク一覧ページから新規タスクを追加し、担当者や期限を設定します。

各タスクの詳細ページで進捗率やメモを更新すると、リアルタイムでグラフが更新されます。

必要に応じて「エクスポート」ボタンから Excel や YAML 形式でデータを取得できます。

管理者はユーザーや組織を管理画面から追加し、ロールや権限レベルを設定できます。

スクリーンショット例:

(ここにアプリのスクリーンショットを挿入します)
ライセンス
このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルをご確認ください。
