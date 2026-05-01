
# タスク進捗リマインダー基盤（Redis × Celery）技術ドキュメント

最終更新: 2025-08-25（JST）

本ドキュメントは、**Redis** と **Celery** を用いたメール自動配信（リマインダー）基盤の設計・運用方法をまとめたものです。対象は 20 名規模のシステムで、**API からの送信は現時点で未実装**、定時ジョブのみを運用します。

---

## 全体像

```
┌──────────────────────────────────────────────────────────┐
│ Flask App (app/)                                        │
│  ├─ util/mailer.py …… SMTP 汎用送信                     │
│  ├─ tasks/notifications.py …… 定時ジョブ本体            │
│  └─ celery_app.py …… Celery アプリ設定（app/celery_app.py） │
└──────────────────────────────────────────────────────────┘
                │            ▲
                │            │  Celery Task 呼び出し
                ▼            │
        ┌──────────────┐  publish/consume  ┌──────────────────┐
        │  Celery Beat │ ─────────────────►│ Celery Worker(s) │
        │ (Scheduler)  │◄──────────────────│  (mail / ai)     │
        └──────────────┘      result       └──────────────────┘
                │
                ▼
        ┌────────────┐
        │   Redis    │  broker（必要に応じて result backend も）
        └────────────┘

        ┌────────────┐
        │ SMTP Server│  実際のメール配信
        └────────────┘
```

- **Beat（スケジューラ）**: 毎朝 9:00（Asia/Tokyo）に `daily_progress_reminder` を発行。
- **Worker（mail キュー）**: 発行されたタスクを受け取り、DB から対象抽出 → `util/mailer.py` で SMTP 送信。
- **Redis**: Celery の **ブローカー**。必要に応じて **結果バックエンド**も Redis を利用。
- **SMTP**: メール送信は Redis を使わず、SMTP で直接配信。

---

## ディレクトリ構成（抜粋）

```
app/
  __init__.py
  celery_app.py                # ★ app/ 配下に配置（-A app.celery_app.celery）
  tasks/
    __init__.py
    notifications.py           # ★ 定時タスク（DB抽出→本文生成→送信）
  util/
    __init__.py
    mailer.py                  # ★ 汎用SMTP送信ユーティリティ
```

### 主要ファイルの役割
- `app/celery_app.py` … Celery 構成（ブローカー、タイムゾーン、キュールーティング、スケジュール）
- `app/tasks/notifications.py` … 定時実行ロジック（ユーザー・タスク抽出、重複抑止、本文生成、送信）
- `app/util/mailer.py` … `MailMessage` / `send_email()`：Return-Path / Reply-To / STARTTLS / SSL / Timeout 対応

---

## 環境変数（.env）例

```env
# Redis / Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1

# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587                  # 465 の場合は SSL
SMTP_USERNAME=app@example.com
SMTP_PASSWORD=********
MAIL_FROM=Task Progress <app@example.com>
MAIL_REPLY_TO=Support <support@example.com>  # 任意
MAIL_RETURN_PATH=bounce@example.com          # 任意
SMTP_TIMEOUT=30
```

> 本番常駐時は **systemd の `EnvironmentFile=`** で読み込ませるのが推奨。開発・手動実行時は `python-dotenv` による `load_dotenv()` でも可。

---

## Celery 設定（`app/celery_app.py`）サンプル

```python
from celery import Celery
from celery.schedules import crontab
import os

celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)

celery.conf.update(
    timezone="Asia/Tokyo",
    broker_connection_retry_on_startup=True,  # 起動順の安定化
    task_routes={
        "app.tasks.notifications.*": {"queue": "mail"},
        "app.tasks.ai.*":            {"queue": "ai"},
    },
    beat_schedule={
        "daily-progress-reminder-09": {
            "task": "app.tasks.notifications.daily_progress_reminder",
            "schedule": crontab(minute=0, hour=9),
            "options": {"queue": "mail"},
        },
    },
)

celery.autodiscover_tasks(["app.tasks"])
```

### 注意
- `schedule` は **`crontab(...)`** や `timedelta(...)` の **オブジェクト**を使用（dict は NG）。
- スケジュール定義を変更したら、**`celerybeat-schedule` を削除**してから再起動。

---

## 定時タスク（`app/tasks/notifications.py`）のポイント

- DB から「未報告タスクがあるユーザー」を抽出。
- 当日重複送信ガード：`Redis.setnx("remind:<user_id>:YYYY-MM-DD","1")` を使い 24h で expire。
- ユーザーの通知設定（将来拡張）:
  - `notify_frequency`: daily / weekly / none
  - `timezone`, `quiet_hours_start`, `quiet_hours_end` で時間帯の抑止
- 送信は `app/util/mailer.py` の `send_email(MailMessage(...))` を利用。

---

## SMTP 送信（`app/util/mailer.py`）の仕様

- `SMTP_PORT=465` なら **SSL**、それ以外は STARTTLS（拡張があれば）へ自動切替。
- `MAIL_FROM`, `MAIL_REPLY_TO`, `MAIL_RETURN_PATH` に対応。
- 件名・表示名は RFC 2047 に基づき UTF-8 エンコード。
- 失敗時は `MailSendError` を送出。

---

## systemd ユニット（常駐化）

`/etc/systemd/system/celery-beat.service`
```ini
[Unit]
Description=Celery Beat Scheduler
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<USER>
WorkingDirectory=/home/<USER>/task-progress-api
EnvironmentFile=/home/<USER>/task-progress-api/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/<USER>/task-progress-api/venv/bin/celery -A app.celery_app.celery beat --loglevel=INFO
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/celery-worker-mail.service`
```ini
[Unit]
Description=Celery Worker (mail queue)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<USER>
WorkingDirectory=/home/<USER>/task-progress-api
EnvironmentFile=/home/<USER>/task-progress-api/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/<USER>/task-progress-api/venv/bin/celery -A app.celery_app.celery worker -Q mail -n mail@%H -c 2 --loglevel=INFO
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/celery-worker-ai.service`
```ini
[Unit]
Description=Celery Worker (ai queue)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<USER>
WorkingDirectory=/home/<USER>/task-progress-api
EnvironmentFile=/home/<USER>/task-progress-api/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/<USER>/task-progress-api/venv/bin/celery -A app.celery_app.celery worker -Q ai -n ai@%H -c 4 --loglevel=INFO
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

> `<USER>` は実行ユーザー名に置換してください。

### 反映コマンド
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now celery-beat.service
sudo systemctl enable --now celery-worker-mail.service
sudo systemctl enable --now celery-worker-ai.service
```

---

## ローカル／CLI テスト

### Beat（前面）
```bash
/path/to/venv/bin/celery -A app.celery_app.celery beat -l INFO
```

### Worker（mail キュー）
```bash
/path/to/venv/bin/celery -A app.celery_app.celery worker -Q mail -l INFO
```

### タスクを即時キック
```bash
/path/to/venv/bin/celery -A app.celery_app.celery call app.tasks.notifications.daily_progress_reminder
```

---

## 運用・保守（Runbook）

- **スケジュール変更後の初回**: `celerybeat-schedule` を削除してから Beat を再起動。
- **Redis 停止時**: `broker_connection_retry_on_startup=True` を有効化。起動直後の接続失敗で落ちる場合は再起動 or 起動順の調整。
- **SMTP 停止時**: `MailSendError` をログ。必要なら Celery の `autoretry_for=[MailSendError]` と `retry_backoff=True` をタスクに付与。
- **ログ確認**:
  ```bash
  journalctl -u celery-beat -f
  journalctl -u celery-worker-mail -f
  ```
- **Redis 健全性**: `redis-cli PING` → `PONG`。
- **キューモニタ**: `celery -A app.celery_app.celery inspect active` / `registered` / `scheduled`。

---

## セキュリティ

- SMTP 認証情報は `.env` / systemd `EnvironmentFile=` から供給。**リポジトリに含めない**。
- メール差出人（`MAIL_FROM`）は実在ドメイン・SPF/DKIM/DMARC の整備を推奨。
- Redis はローカル or VPC 内で運用。外部公開は避ける（必要時はパスワード・TLS）。

---

## スケール／将来拡張

- **ワーカー分離**（既に mail / ai でキュー分離）により、AI の重負荷がメール遅延に干渉しにくい。
- 送信履歴・再送制御が必要になれば **Outbox テーブル**導入を検討。
- 祝日スキップ・週次ダイジェスト（`weekly_progress_digest`）など、Beat のスケジュールを追加可能。

---

## トラブルシューティング（FAQ）

- **`ModuleNotFoundError: No module named 'app'`**  
  → `celery_app.py` を **`app/` 配下**へ移し、`-A app.celery_app.celery` で起動。`app/__init__.py` と `app/tasks/__init__.py` を配置。

- **`'dict' object has no attribute 'app'`（beat 起動時）**  
  → `beat_schedule` の `schedule` に **dict を設定している**のが原因。`crontab(...)` / `timedelta(...)` オブジェクトに修正。既存の `celerybeat-schedule` を削除して再起動。

- **`.env はいつ読まれる？`**  
  → Flask CLI 以外は自動ロードされません。手動実行時は `python-dotenv` の `load_dotenv()` を使用。本番は systemd の `EnvironmentFile=` 推奨。

- **Redis は何個必要？**  
  → **1 サービスで OK**。`/0` を broker、`/1` を backend など論理 DB を分けると運用しやすい。

---

## 付録：開発メモ

- 依存：`celery`, `redis`, `python-dotenv`
- venv でのインストール：
  ```bash
  pip install celery redis python-dotenv
  ```
- バージョン一例：
  - Python 3.12
  - Celery 5.5.x
  - Redis 6.x+

---

以上。
