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

# 環境変数ファイルを作成 (.env.example をコピー)

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

# API 基底 URL を指定する場合は .env ファイルを作成（例）

echo "VITE_API_BASE_URL=http://localhost:5000" > .env
echo "VITE_OPENAPI_URL=http://localhost:5000/openapi.json" >> .env

# OpenAPI 仕様から API クライアントを生成

npm run generate:api

# フロントエンド開発サーバー起動

npm run dev
Docker による統合起動 (任意)

リポジトリには docker-compose.yml と docker-compose.prod.yml が含まれており、MySQL、Redis、Flask、React アプリをまとめて起動できます。

docker compose up --build
本番用設定では docker-compose.prod.yml を利用してください。

主要な環境変数
バックエンドの config.py では多数の環境変数を読み込みます。最低限必要なものは以下です。

変数名 用途
DATABASE_URL SQLAlchemy に渡す DB 接続文字列 (例: mysql+pymysql://user:pass@localhost/progress_db)
SECRET_KEY セッションやCSRFトークンに使用する秘密鍵
FRONTEND_URL CORS 設定で許可するフロントエンドの URL (デフォルト http://localhost:5173)
CORS_ORIGINS アクセスを許可するドメインのカンマ区切りリスト
API_TITLE / API_VERSION OpenAPI ドキュメントのタイトルとバージョン
CELERY_BROKER_URL / CELERY_RESULT_BACKEND 非同期ジョブ用のブローカー（通常は Redis）
SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD メール送信に利用する SMTP サーバー情報
GOOGLE_API_KEY / GEMINI_MODEL Gemini API を利用する場合のキーとモデル名
フロントエンドでは、以下の環境変数を .env に設定します:

変数名 用途
VITE_API_BASE_URL バックエンド API のベース URL (例: http://localhost:5000)
VITE_OPENAPI_URL OpenAPI JSON の URL (例: http://localhost:5000/openapi.json)
プロジェクト構成
task-progress-manager-monorepo/
├── backend/ # Flask API (task progress 管理)
│ ├── app/ # モデル・ルート・サービス・スキーマ
│ ├── migrations/ # Alembic マイグレーション
│ ├── docs/ # 設計や権限仕様のドキュメント
│ ├── .env.example # 環境変数サンプル
│ ├── requirements.txt
│ └── run.py # アプリケーションのエントリポイント
├── frontend/ # React + Vite SPA
│ ├── src/ # コンポーネント、ページ、hooks 等
│ ├── public/ # 静的ファイル
│ ├── orval.config.ts # OpenAPI からクライアント生成する設定
│ └── README.md # フロントエンド固有のドキュメント
├── docker-compose.yml # 開発用 docker compose 設定
├── docker-compose.prod.yml # 本番用 docker compose 設定
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
