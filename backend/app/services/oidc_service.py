from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from authlib.integrations.base_client.errors import MismatchingStateError, OAuthError
from joserfc.errors import JoseError
from flask import current_app, request
from flask_login import login_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db, oauth
from app.models import User
from app.service_errors import ServiceAuthenticationError, ServicePermissionError


OIDC_ERROR_MESSAGES = {
    "configuration_error": "Common Identity Hubの設定が完了していません。",
    "provider_failure": "Common Identity Hubでのログインに失敗しました。",
    "invalid_state": "認証リクエストが無効です。再度ログインしてください。",
    "token_exchange_failure": "Common Identity Hubでのログインに失敗しました。",
    "invalid_id_token": "Common Identity Hubの認証情報を確認できませんでした。",
    "user_not_registered": (
        "Common Identity Hubへのログインには成功しましたが、"
        "Task Progress Managerの利用登録がありません。管理者にお問い合わせください。"
    ),
    "email_not_verified": "メールアドレスが未検証のため、安全上アカウントを連携できません。",
    "identity_conflict": "このCommon Identity Hubアカウントは別のユーザーに連携されています。",
    "user_unavailable": "このユーザーは現在利用できません。",
}


class OIDCFlowError(ServiceAuthenticationError):
    def __init__(self, error_code: str):
        self.error_code = error_code
        super().__init__(OIDC_ERROR_MESSAGES[error_code])


class OIDCAccessDeniedError(ServicePermissionError):
    def __init__(self, error_code: str):
        self.error_code = error_code
        super().__init__(OIDC_ERROR_MESSAGES[error_code])


def _require_oidc_config() -> None:
    required = (
        "OIDC_ISSUER_URL",
        "OIDC_CLIENT_ID",
        "OIDC_CLIENT_SECRET",
        "OIDC_REDIRECT_URI",
        "OIDC_FRONTEND_REDIRECT_URL",
    )
    if any(not current_app.config.get(name) for name in required):
        raise OIDCFlowError("configuration_error")


def get_oidc_client() -> Any:
    _require_oidc_config()
    client = oauth.create_client("cih")
    if client is None:
        raise OIDCFlowError("configuration_error")
    return client


def begin_login() -> Any:
    client = get_oidc_client()
    try:
        return client.authorize_redirect(current_app.config["OIDC_REDIRECT_URI"])
    except Exception:
        current_app.logger.warning("Unable to start the OIDC authorization flow")
        raise OIDCFlowError("provider_failure") from None


def _is_available(user: User) -> bool:
    return not user.is_deleted and bool(user.is_active)


def _resolve_user(claims: dict[str, Any]) -> User:
    issuer = claims.get("iss")
    subject = claims.get("sub")
    if not isinstance(issuer, str) or not issuer or not isinstance(subject, str) or not subject:
        raise OIDCFlowError("invalid_id_token")

    if issuer.rstrip("/") != current_app.config["OIDC_ISSUER_URL"]:
        raise OIDCFlowError("invalid_id_token")

    linked_user = User.query.filter_by(
        identity_issuer=issuer,
        identity_subject=subject,
    ).first()
    if linked_user is not None:
        if not _is_available(linked_user):
            raise OIDCAccessDeniedError("user_unavailable")
        return linked_user

    if claims.get("email_verified") is not True:
        raise OIDCAccessDeniedError("email_not_verified")

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        raise OIDCAccessDeniedError("user_not_registered")

    candidates = User.query.filter_by(
        normalized_email=User._normalize(email),
    ).all()
    available_users = [user for user in candidates if _is_available(user)]

    if not available_users:
        if candidates:
            raise OIDCAccessDeniedError("user_unavailable")
        raise OIDCAccessDeniedError("user_not_registered")
    if len(available_users) != 1:
        raise OIDCAccessDeniedError("identity_conflict")

    user = available_users[0]
    if user.identity_issuer is not None or user.identity_subject is not None:
        raise OIDCAccessDeniedError("identity_conflict")

    user.identity_issuer = issuer
    user.identity_subject = subject
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise OIDCAccessDeniedError("identity_conflict") from None
    return user


def complete_login() -> User:
    if request.args.get("error"):
        raise OIDCFlowError("provider_failure")

    client = get_oidc_client()
    try:
        token = client.authorize_access_token()
    except MismatchingStateError:
        raise OIDCFlowError("invalid_state") from None
    except JoseError:
        raise OIDCFlowError("invalid_id_token") from None
    except OAuthError:
        raise OIDCFlowError("token_exchange_failure") from None
    except Exception:
        current_app.logger.warning("OIDC token processing failed")
        raise OIDCFlowError("provider_failure") from None

    claims = token.get("userinfo") if isinstance(token, dict) else None
    if claims is None:
        raise OIDCFlowError("invalid_id_token")

    user = _resolve_user(dict(claims))
    login_user(user)
    return user


def frontend_redirect_url(error_code: str | None = None) -> str:
    target = current_app.config["OIDC_FRONTEND_REDIRECT_URL"]
    if not error_code:
        return target

    parts = urlsplit(target)
    path = parts.path.rstrip("/")
    if not path.endswith("/login"):
        path = f"{path}/login" if path else "/login"
    query = urlencode({"oidc_error": error_code})
    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))
