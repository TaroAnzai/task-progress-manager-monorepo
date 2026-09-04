from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from authlib.integrations.base_client.errors import MismatchingStateError, OAuthError
from joserfc.errors import JoseError
from flask import redirect
from werkzeug.security import generate_password_hash

from app import db
from app.models import User
from app.services import oidc_service


ISSUER = "https://auth.example.test/realms/anzai-home"
FRONTEND_URL = "https://tpm.example.test/"


class FakeOIDCClient:
    def __init__(self, claims: dict[str, Any] | None = None, error: Exception | None = None):
        self.claims = claims
        self.error = error

    def authorize_redirect(self, redirect_uri: str):
        return redirect(f"https://auth.example.test/authorize?redirect_uri={redirect_uri}")

    def authorize_access_token(self):
        if self.error is not None:
            raise self.error
        return {"userinfo": self.claims}


@pytest.fixture(autouse=True)
def oidc_config(app):
    app.config.update(
        OIDC_ISSUER_URL=ISSUER,
        OIDC_CLIENT_ID="task-progress-manager",
        OIDC_CLIENT_SECRET="test-secret",
        OIDC_REDIRECT_URI="https://api.example.test/sessions/oidc/callback",
        OIDC_FRONTEND_REDIRECT_URL=FRONTEND_URL,
    )


@pytest.fixture(autouse=True)
def clear_login_session(client):
    with client.session_transaction() as flask_session:
        flask_session.clear()
    yield
    with client.session_transaction() as flask_session:
        flask_session.clear()


def _user(
    email: str,
    *,
    issuer: str | None = None,
    subject: str | None = None,
    deleted: bool = False,
) -> User:
    user = User(
        name="OIDC User",
        email=email,
        password_hash=generate_password_hash("local-password"),
        identity_issuer=issuer,
        identity_subject=subject,
        is_deleted=deleted,
    )
    db.session.add(user)
    db.session.flush()
    return user


def _mock_client(monkeypatch, claims=None, error=None):
    client = FakeOIDCClient(claims=claims, error=error)
    monkeypatch.setattr(oidc_service, "get_oidc_client", lambda: client)
    return client


def _claims(**overrides):
    claims = {
        "iss": ISSUER,
        "sub": "cih-subject",
        "email": "linked@example.com",
        "email_verified": True,
    }
    claims.update(overrides)
    return claims


def test_oidc_login_redirects_to_provider(client, monkeypatch):
    _mock_client(monkeypatch)

    response = client.get("/sessions/oidc/login")

    assert response.status_code == 302
    assert response.location.startswith("https://auth.example.test/authorize")
    assert "sessions/oidc/callback" in response.location


def test_oidc_linked_user_logs_in(client, monkeypatch):
    user = _user("linked@example.com", issuer=ISSUER, subject="cih-subject")
    _mock_client(monkeypatch, _claims())

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert response.status_code == 302
    assert response.location == FRONTEND_URL
    current = client.get("/sessions/current").get_json()
    assert current["id"] == user.id


def test_oidc_first_login_links_verified_email(client, monkeypatch):
    user = _user("Linked@Example.com")
    _mock_client(monkeypatch, _claims(email=" linked@example.com "))

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert response.status_code == 302
    assert user.identity_issuer == ISSUER
    assert user.identity_subject == "cih-subject"
    assert client.get("/sessions/current").get_json()["id"] == user.id


def test_oidc_unverified_email_is_not_linked(client, monkeypatch):
    user = _user("linked@example.com")
    _mock_client(monkeypatch, _claims(email_verified=False))

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert response.status_code == 302
    assert "oidc_error=email_not_verified" in response.location
    assert user.identity_issuer is None
    assert user.identity_subject is None


def test_oidc_user_without_tpm_registration_is_denied(client, monkeypatch):
    before = User.query.count()
    _mock_client(monkeypatch, _claims(email="missing@example.com"))

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert "oidc_error=user_not_registered" in response.location
    assert User.query.count() == before


def test_oidc_does_not_replace_another_identity(client, monkeypatch):
    user = _user("linked@example.com", issuer=ISSUER, subject="another-subject")
    _mock_client(monkeypatch, _claims())

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert "oidc_error=identity_conflict" in response.location
    assert user.identity_subject == "another-subject"


@pytest.mark.parametrize(
    ("issuer", "subject"),
    [
        (ISSUER, "cih-subject"),
        (None, None),
    ],
)
def test_oidc_deleted_user_is_denied(client, monkeypatch, issuer, subject):
    user = _user("linked@example.com", issuer=issuer, subject=subject, deleted=True)
    _mock_client(monkeypatch, _claims())

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert "oidc_error=user_unavailable" in response.location
    assert client.get("/sessions/current").get_json()["id"] is None


def test_oidc_state_mismatch_is_reported(client, monkeypatch):
    _mock_client(monkeypatch, error=MismatchingStateError())

    response = client.get("/sessions/oidc/callback?code=code&state=invalid")

    assert response.status_code == 302
    assert "oidc_error=invalid_state" in response.location


def test_oidc_logout_only_clears_flask_session(client, monkeypatch):
    _user("linked@example.com", issuer=ISSUER, subject="cih-subject")
    _mock_client(monkeypatch, _claims())
    client.get("/sessions/oidc/callback?code=code&state=state")

    response = client.delete("/sessions/current")

    assert response.status_code == 200
    assert client.get("/sessions/current").get_json()["id"] is None



def test_oidc_login_uses_state_nonce_and_pkce(client, monkeypatch):
    real_client = oidc_service.oauth.create_client("cih")
    real_client.client_id = "task-progress-manager"
    real_client.client_secret = "test-secret"
    monkeypatch.setattr(
        real_client,
        "load_server_metadata",
        lambda: {
            "issuer": ISSUER,
            "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
        },
    )
    monkeypatch.setattr(oidc_service, "get_oidc_client", lambda: real_client)

    response = client.get("/sessions/oidc/login")

    assert response.status_code == 302
    query = parse_qs(urlsplit(response.location).query)
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["task-progress-manager"]
    assert query["scope"] == ["openid email profile"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"][0]
    assert query["nonce"][0]
    assert query["state"][0]

    with client.session_transaction() as flask_session:
        state_data = flask_session[f"_state_cih_{query['state'][0]}"]["data"]
        assert state_data["nonce"] == query["nonce"][0]
        assert state_data["code_verifier"]


@pytest.mark.parametrize(
    ("error", "error_code"),
    [
        (OAuthError(error="invalid_grant"), "token_exchange_failure"),
        (JoseError("invalid token"), "invalid_id_token"),
    ],
)
def test_oidc_callback_hides_protocol_errors(client, monkeypatch, error, error_code):
    _mock_client(monkeypatch, error=error)

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert response.status_code == 302
    assert f"oidc_error={error_code}" in response.location
    assert "invalid_grant" not in response.location
    assert "invalid+token" not in response.location


def test_oidc_rejects_unexpected_issuer(client, monkeypatch):
    user = _user("linked@example.com")
    _mock_client(monkeypatch, _claims(iss="https://attacker.example/realms/other"))

    response = client.get("/sessions/oidc/callback?code=code&state=state")

    assert "oidc_error=invalid_id_token" in response.location
    assert user.identity_issuer is None
