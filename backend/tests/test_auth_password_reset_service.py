from datetime import timedelta

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import User
from app.service_errors import ServiceValidationError
from app.services import auth_password_reset_service as service
from app.util.mailer import MailSendError


@pytest.fixture
def reset_sample_user(root_org):
    user = User(name="Reset User", email="service-reset@example.com",
                organization_id=root_org["id"])
    user.set_password("old password")
    db.session.add(user); db.session.flush()
    return {"id": user.id, "email": user.email}


def test_request_rejects_blank_email():
    with pytest.raises(ServiceValidationError, match="不正"):
        service.request_password_reset({"email": "  "})


def test_request_hides_database_lookup_failure(monkeypatch):
    monkeypatch.setattr(db.session, "execute", lambda *_: (_ for _ in ()).throw(SQLAlchemyError("db unavailable")))
    assert service.request_password_reset({"email": "unknown@example.com"}) == "Send mail"


def test_request_rolls_back_commit_failure(monkeypatch, reset_sample_user):
    monkeypatch.setattr(service, "send_email", lambda *_: None)
    monkeypatch.setattr(db.session, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("commit failed")))
    assert service.request_password_reset({"email": reset_sample_user["email"]}) == "Send mail"


def test_request_keeps_generic_success_when_mail_fails(monkeypatch, reset_sample_user):
    monkeypatch.setattr(service, "send_email", lambda *_: (_ for _ in ()).throw(MailSendError("smtp down")))
    assert service.request_password_reset({"email": reset_sample_user["email"]}) == "メールを送信しました。"


@pytest.mark.parametrize("data", [{}, {"token": "x"}, {"new_password": "new password"}])
def test_confirm_requires_token_and_password(data):
    with pytest.raises(ServiceValidationError, match="無効なリクエスト"):
        service.confirm_password_reset(data)


def test_confirm_rejects_token_without_email(monkeypatch):
    monkeypatch.setattr(service, "_verify_token", lambda *_args, **_kwargs: {"v": 1})
    with pytest.raises(ServiceValidationError, match="期限切れ"):
        service.confirm_password_reset({"token": "token", "new_password": "new password"})


def test_confirm_rejects_blank_email_in_token(monkeypatch):
    monkeypatch.setattr(service, "_verify_token", lambda *_args, **_kwargs: {"email": " "})
    with pytest.raises(ServiceValidationError, match="期限切れ"):
        service.confirm_password_reset({"token": "token", "new_password": "new password"})


def test_confirm_rejects_validly_signed_token_for_missing_user():
    token = service._generate_token("missing-reset@example.com")
    with pytest.raises(ServiceValidationError, match="期限切れ"):
        service.confirm_password_reset({"token": token, "new_password": "new password"})


@pytest.mark.parametrize("invalid_state", ["hash", "expiry", "expired", "used"])
def test_confirm_rejects_invalid_saved_token_state(reset_sample_user, invalid_state):
    user = db.session.get(User, reset_sample_user["id"])
    token = service._generate_token(user.normalized_email)
    user.password_reset_token_hash = service._hash_token(token)
    user.password_reset_expires_at = service._now_utc_naive() + timedelta(minutes=5)
    user.password_reset_used = False
    if invalid_state == "hash": user.password_reset_token_hash = "wrong"
    elif invalid_state == "expiry": user.password_reset_expires_at = None
    elif invalid_state == "expired": user.password_reset_expires_at = service._now_utc_naive() - timedelta(seconds=1)
    else: user.password_reset_used = True
    db.session.flush()
    with pytest.raises(ServiceValidationError, match="期限切れ"):
        service.confirm_password_reset({"token": token, "new_password": "new password"})


def test_confirm_translates_database_failure(monkeypatch):
    token = service._generate_token("db-reset@example.com")
    monkeypatch.setattr(db.session, "execute", lambda *_: (_ for _ in ()).throw(SQLAlchemyError("db unavailable")))
    with pytest.raises(ServiceValidationError, match="更新に失敗"):
        service.confirm_password_reset({"token": token, "new_password": "new password"})
