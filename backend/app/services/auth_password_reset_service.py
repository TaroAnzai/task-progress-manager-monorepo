
from __future__ import annotations
import os

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import logging
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from flask import current_app, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from app.models import db, User
from app.service_errors import (
    ServiceValidationError,
    ServicePermissionError,
    ServiceAuthenticationError,
    ServiceNotFoundError,
)
from app.util.mailer import MailConfig, MailMessage, send_email, MailSendError
# ---------- Config（期限などを一元管理したい場合） ----------
TOKEN_MAX_AGE_MINUTE = 30
DEFAULT_TOKEN_MAX_AGE_SECONDS = int(timedelta(minutes=TOKEN_MAX_AGE_MINUTE).total_seconds())
DOMAIN_URL = "https://anzai-home.com"

_SALT = "password-reset"  # 用途ごとに salt を分離


# Load Template
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "util", "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml", "txt"])
)
text_template = env.get_template("pw_reset_mail.txt")
html_template = env.get_template("pw_reset_mail.html")

def _now_utc_naive() -> datetime:
    """DBはnaive UTCで統一保存する前提。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt=_SALT,
    )

def _generate_token(email_normalized: str) -> str:
    """ペイロードは最小限。必要ならバージョン等を追加可。"""
    s = _get_serializer()
    return s.dumps({"email": email_normalized, "v": 1})

def _verify_token(raw_token: str, max_age_seconds: int) -> Optional[dict]:
    s = _get_serializer()
    try:
        return s.loads(raw_token, max_age=max_age_seconds)
    except (SignatureExpired, BadSignature):
        return None

def _hash_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()

def _build_reset_url(request_host_url: str, raw_token: str) -> str:
    """
    React側のリセット画面（例）：/reset-password?token=...
    request_host_url は Flask の request.host_url を想定（末尾スラッシュ除去推奨）
    """
    base = request_host_url.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


# ---------- Service Function ----------

def request_password_reset(data):
    """
    パスワードリセット要求を受け付け、トークンを発行してメール送信する。
    - メールが存在しない場合も同じ挙動（情報漏洩対策）
    - 既存の token_hash は上書き（最新のみ有効）
    """
    normalized = (data['email'] or "").strip().lower()
    if not normalized:
        # 形式はルート層のSchemaで弾かれている想定だが、ここでも安全にreturn
        raise ServiceValidationError("メールアドレスが不正です。")

    try:
        user: Optional[User] = db.session.execute(
            select(User).where(User.normalized_email == normalized)
        ).scalar_one_or_none()
    except SQLAlchemyError:
        # 存在有無を外に漏らさない
        current_app.logger.error("DB error while finding user for password reset")
        return "Send mail"
    # ユーザーが居なくても成功扱い
    if not user:
        return "Send mail"

    # トークン生成＆保存
    raw_token = _generate_token(user.normalized_email)
    token_hash = _hash_token(raw_token)
    now = _now_utc_naive()

    # 期限は max_age_seconds に一致させる
    user.password_reset_token_hash = token_hash
    user.password_reset_expires_at = now + timedelta(seconds=DEFAULT_TOKEN_MAX_AGE_SECONDS)
    user.password_reset_used = False
    try:
        db.session.commit()
    except SQLAlchemyError:
        current_app.logger.error("DB commit failed in request_password_reset (user_id=%s)", user.id)
        # 失敗しても存在有無は出さない
        db.session.rollback()
        return "Send mail"

    # --- 本文生成 ---
    domain_url = current_app.config.get("FRONTEND_URL", DOMAIN_URL).rstrip("/")
    url_prefix = current_app.config.get("URL_PREFIX", "")
    reset_url_prefix = domain_url + '/' + url_prefix

    context = {
        "user_name": user.name,
        "reset_url": _build_reset_url(reset_url_prefix, raw_token),
        "expires_minutes": TOKEN_MAX_AGE_MINUTE,
        "support_email": "support@anzai-home.com",
        "app_name": "Task Progress Manager",
        "brand_logo_url": "https://www.anzai-home.com/blog/wp-content/uploads/2025/03/cropped-Anzai-Home-Icon.jpg",
        "request_ip": "203.0.113.10",
        "request_time": "2025-09-01 16:20 JST",
        "domain": "anzai-home.com",
    }
    body_text = text_template.render(**context)
    body_html = html_template.render(**context)



    # メール送信（失敗してもログのみ・存在有無は漏らさない）
    try:
        msg = MailMessage(
            subject="【Task Progress Manager】パスワード再設定 / Password Reset",
            to=[user.email],   # ✅ 宛先
            text=body_text,  # ✅ プレーンテキスト本文
            html=body_html   # ✅ HTML本文
        )
        mail_config = MailConfig.from_config(current_app.config)
        send_email(msg, mail_config)
    except MailSendError as e:  # pragma: no cover
        current_app.logger.error(f"Failed to send email to {user.email}: {e}")
        # メール送信失敗でもAPIは同文言で返す想定（ルート層）
    return "メールを送信しました。"


def confirm_password_reset(data):
    """
    受け取ったトークンと新パスワードを検証し、パスワードを更新する。
    エラー時は BadRequest を投げる（ルート層で 400 に変換）。
    """
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""
    if not token or not new_password:
        raise ServiceValidationError("無効なリクエストです。")

    res_verify_token = _verify_token(data['token'], max_age_seconds=DEFAULT_TOKEN_MAX_AGE_SECONDS)
    if not res_verify_token or "email" not in res_verify_token:
        raise ServiceValidationError("トークンが無効または期限切れです。")

    normalized = (res_verify_token["email"] or "").strip().lower()
    if not normalized:
        raise ServiceValidationError("トークンが無効または期限切れです。")

    # 以降は厳密なワンタイム性確保のためトランザクション＋ロック
    try:
        # FOR UPDATE ロックで二重処理を防止
        user = db.session.execute(
            select(User)
            .where(User.normalized_email == normalized)
            .with_for_update()
        ).scalar_one_or_none()
        if not user:
            raise ServiceValidationError("トークンが無効または期限切れです。")

        now = _now_utc_naive()
        incoming_hash = _hash_token(data['token'])

        # ステートフル検証：ハッシュ一致・期限内・未使用
        if (
            not user.password_reset_token_hash
            or user.password_reset_token_hash != incoming_hash
            or not user.password_reset_expires_at
            or user.password_reset_expires_at < now
            or user.password_reset_used
        ):
            raise ServiceValidationError("トークンが無効または期限切れです。")

        # パスワード更新（プロジェクト方針に合わせて set_password があれば使用）
        # ここでは既存方針に合わせて generate_password_hash を直接適用
        user.set_password(data['new_password'])

        # 使用済み化＆後片付け（再利用防止）
        user.password_reset_used = True
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None

        db.session.commit()
    except ServiceValidationError:
        # 業務エラーはそのまま
        db.session.rollback()
        raise
    except SQLAlchemyError as e:
        db.session.rollback()
        print("SQLAlchemyError",e)
        current_app.logger.error("DB error in confirm_password_reset (email=%s)", normalized)
        raise ServiceValidationError("パスワード更新に失敗しました。もう一度お試しください。")