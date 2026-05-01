# =========================
# Base Image
# =========================
FROM python:3.11-slim

# =========================
# 環境変数
# =========================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =========================
# 作業ディレクトリ
# =========================
WORKDIR /app

# =========================
# システムパッケージ（MySQLクライアント等）
# =========================
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Python依存関係
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# アプリケーションコピー
# =========================
COPY . .

# =========================
# ポート
# =========================
EXPOSE 8000

# =========================
# 起動コマンド
# =========================
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]