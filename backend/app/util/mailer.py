# app/util/mailer.py
"""
汎用メール送信ユーティリティ（SMTP）

- 依存：標準ライブラリのみ（smtplib, email.*）
- 設計：
    設定は MailConfig（DTO）として受け取り、環境変数やFlaskには依存しない
    → 呼び出し側（service等）で設定を組み立てて渡す

- 必須設定（MailConfig）：
    host            : SMTPサーバー
    port            : ポート番号
    mail_from       : 送信元アドレス

- 任意設定（MailConfig）：
    user            : SMTP認証ユーザー名
    password        : SMTP認証パスワード
    mail_reply_to   : デフォルト返信先
    mail_return_path: バウンスメール送信先
    timeout         : 接続タイムアウト（秒）

- 使い方：
    from app.util.mailer import MailMessage, MailConfig, send_email

    config = MailConfig(
        host="smtp.example.com",
        port=587,
        user="user",
        password="pass",
        mail_from="noreply@example.com"
    )

    msg = MailMessage(
        to=["user@example.com"],
        subject="Hello",
        text="Hi"
    )

    send_email(msg, config)

- 備考：
    - user が指定されている場合のみ SMTP認証を行う
    - Reply-To は MailMessage または MailConfig で指定可能
    - Return-Path は MailConfig で制御する（Reply-Toとは別）
"""

from __future__ import annotations

import smtplib
import socket
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid


class MailSendError(Exception):
    """メール送信に失敗した場合に送出される例外。"""
@dataclass
@dataclass
class MailConfig:
    host: str
    port: int
    mail_from: str
    user: str | None
    password: str | None
    timeout: int = 30
    mail_reply_to: Optional[str] = None
    mail_return_path: Optional[str] = None


    @classmethod
    def from_config(cls, config: Mapping[str, Any]):
        host = config.get("SMTP_HOST")
        if not host:
            raise ValueError("SMTP_HOST is required")

        port = config.get("SMTP_PORT")
        if not isinstance(port, int):
            raise ValueError("SMTP_PORT must be int")
        mail_from = config.get("MAIL_FROM") or config.get("SMTP_USERNAME")
        if not mail_from:
            raise ValueError("MAIL_FROM or SMTP_USERNAME must be configured.")
        return cls(
            host=host,
            port=port,
            mail_from=mail_from,
            user=config.get("SMTP_USERNAME"),
            password=config.get("SMTP_PASSWORD"),
            timeout=int(config.get("SMTP_TIMEOUT", 30)),
            mail_reply_to=config.get("MAIL_REPLY_TO"),
            mail_return_path=config.get("MAIL_RETURN_PATH"),
        )

@dataclass
class MailMessage:
    """
    送信メッセージ定義。

    Attributes:
        to: 宛先（必須）
        subject: 件名（必須）
        text: プレーンテキスト本文
        html: HTML本文（任意）
        reply_to: 返信先（"Name <addr>" または "addr"）
        cc: Cc 宛先
        bcc: Bcc 宛先（ヘッダには含めない）
    """
    def __init__(
        self,
        to: list[str],                 # ✅ list[str] に統一
        subject: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ):
        self.to = to
        self.subject = subject
        self.text = text
        self.html = html
        self.reply_to = reply_to
        self.cc = cc or []
        self.bcc = bcc or []


def _fmt(addr: str) -> str:
    """'表示名 <addr>' または 'addr' をRFC 2047に則って整形。"""
    if "<" in addr and ">" in addr:
        name, email = addr.split("<", 1)
        return formataddr((str(Header(name.strip(), "utf-8")), email.strip(" >")))
    return addr


def _connect(config: MailConfig) -> smtplib.SMTP:
    """SMTPへ接続して、必要に応じてSTARTTLS/LOGINまで実施して返す。"""
    host = config.host
    if not host:
        raise MailSendError("SMTP_HOST is not configured.")

    port = config.port or 587
    user = config.user
    pw = config.password
    timeout = config.timeout
    try:
        if port == 465:
            smtp = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(host, port, timeout=timeout)
            smtp.ehlo()
            if smtp.has_extn("STARTTLS"):
                smtp.starttls()
                smtp.ehlo()

        if user and pw:
            smtp.login(user, pw)

        return smtp
    except (socket.timeout, smtplib.SMTPException) as e:
        raise MailSendError(f"SMTP connect/login failed: {e}") from e


def send_email(msg: MailMessage, config: MailConfig) -> str:
    """
    メールを送信する。
    戻り値: provider_message_id（SMTPでは固定 'smtp:ok'）

    例外:
        MailSendError: 接続/送信/設定不備などの失敗時
    """
    if not msg.to:
        raise MailSendError("No recipients: 'to' is empty.")

    mail_from = config.mail_from
    reply_to = msg.reply_to or config.mail_reply_to or mail_from
    return_path = config.mail_return_path or mail_from

    # メッセージ構築（alternative: text + html）
    m = MIMEMultipart("alternative")
    m["Subject"] = str(Header(msg.subject, "utf-8"))
    m["From"] = _fmt(mail_from)
    m["To"] = ", ".join(_fmt(a) for a in msg.to)
    if msg.cc:
        m["Cc"] = ", ".join(_fmt(a) for a in msg.cc)
    if reply_to:
        m["Reply-To"] = _fmt(reply_to)
    m["Message-ID"] = make_msgid()

    # 本文
    m.attach(MIMEText(msg.text or "", "plain", "utf-8"))
    if msg.html:
        m.attach(MIMEText(msg.html, "html", "utf-8"))

    # 実際に送る宛先（Bcc含む）
    rcpt = list(msg.to) + (msg.cc or []) + (msg.bcc or [])

    try:
        smtp = _connect(config)
        smtp.sendmail(return_path, rcpt, m.as_string())
        smtp.quit()
        return "smtp:ok"
    except Exception as e:
        raise MailSendError(f"Failed to send email to {rcpt}: {e}") from e
