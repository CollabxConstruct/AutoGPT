import time
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from backend.data.model import OAuth2Credentials
from backend.integrations.oauth.base import BaseOAuthHandler
from backend.integrations.providers import ProviderName


class ConcreteOAuthHandler(BaseOAuthHandler):
    PROVIDER_NAME = ProviderName.GITHUB
    DEFAULT_SCOPES = ["read", "write"]

    def __init__(self):
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.redirect_uri = "http://localhost/callback"

    def get_login_url(
        self, scopes: list[str], state: str, code_challenge: Optional[str]
    ) -> str:
        return "https://example.com/login"

    async def exchange_code_for_tokens(
        self, code: str, scopes: list[str], code_verifier: Optional[str]
    ) -> OAuth2Credentials:
        return _make_credentials()

    async def _refresh_tokens(
        self, credentials: OAuth2Credentials
    ) -> OAuth2Credentials:
        return credentials.model_copy(
            update={"access_token": SecretStr("new_access_token")}
        )

    async def revoke_tokens(self, credentials: OAuth2Credentials) -> bool:
        return True


def _make_credentials(
    provider: str = "github",
    access_token: str = "test_access_token",
    access_token_expires_at: Optional[int] = None,
    refresh_token: Optional[str] = None,
) -> OAuth2Credentials:
    return OAuth2Credentials(
        provider=provider,
        access_token=SecretStr(access_token),
        access_token_expires_at=access_token_expires_at,
        refresh_token=SecretStr(refresh_token) if refresh_token else None,
        scopes=["read"],
    )


class TestNeedsRefresh:
    def test_needs_refresh_not_expired(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(
            access_token_expires_at=int(time.time()) + 600
        )
        assert handler.needs_refresh(credentials) is False

    def test_needs_refresh_expired(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(
            access_token_expires_at=int(time.time()) + 100
        )
        assert handler.needs_refresh(credentials) is True

    def test_needs_refresh_no_expiry(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(access_token_expires_at=None)
        assert handler.needs_refresh(credentials) is False


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_tokens_correct_provider(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(provider="github")
        result = await handler.refresh_tokens(credentials)
        assert result.access_token.get_secret_value() == "new_access_token"

    @pytest.mark.asyncio
    async def test_refresh_tokens_wrong_provider(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(provider="notion")
        with pytest.raises(ValueError, match="can not refresh tokens"):
            await handler.refresh_tokens(credentials)


class TestGetAccessToken:
    @pytest.mark.asyncio
    async def test_get_access_token_no_refresh_needed(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(
            access_token="current_token",
            access_token_expires_at=int(time.time()) + 600,
        )
        token = await handler.get_access_token(credentials)
        assert token == "current_token"

    @pytest.mark.asyncio
    async def test_get_access_token_refresh_needed(self):
        handler = ConcreteOAuthHandler()
        credentials = _make_credentials(
            access_token="old_token",
            access_token_expires_at=int(time.time()) + 100,
        )
        token = await handler.get_access_token(credentials)
        assert token == "new_access_token"


class TestHandleDefaultScopes:
    def test_handle_default_scopes_empty(self):
        handler = ConcreteOAuthHandler()
        result = handler.handle_default_scopes([])
        assert result == ["read", "write"]

    def test_handle_default_scopes_provided(self):
        handler = ConcreteOAuthHandler()
        result = handler.handle_default_scopes(["custom_scope"])
        assert result == ["custom_scope"]
