from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from backend.data.model import OAuth2Credentials
from backend.integrations.oauth.notion import NotionOAuthHandler
from backend.integrations.providers import ProviderName


def _make_handler() -> NotionOAuthHandler:
    return NotionOAuthHandler(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost/callback",
    )


def _make_credentials(
    access_token: str = "ntn_test_token",
) -> OAuth2Credentials:
    return OAuth2Credentials(
        provider=ProviderName.NOTION,
        access_token=SecretStr(access_token),
        access_token_expires_at=None,
        refresh_token=None,
        scopes=[],
    )


class TestGetLoginUrl:
    def test_get_login_url(self):
        handler = _make_handler()
        url = handler.get_login_url(scopes=[], state="test_state", code_challenge=None)
        assert "client_id=test_client_id" in url
        assert "redirect_uri=" in url
        assert "state=test_state" in url
        assert "response_type=code" in url
        assert url.startswith("https://api.notion.com/v1/oauth/authorize?")


class TestExchangeCodeForTokens:
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens(self):
        handler = _make_handler()

        token_data = {
            "access_token": "ntn_new_token",
            "token_type": "bearer",
            "bot_id": "bot_123",
            "workspace_id": "ws_456",
            "workspace_name": "Test Workspace",
            "workspace_icon": None,
            "owner": {
                "type": "user",
                "person": {"email": "user@example.com"},
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = token_data

        with patch(
            "backend.integrations.oauth.notion.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler.exchange_code_for_tokens(
                code="test_code", scopes=[], code_verifier=None
            )

        assert result.provider == ProviderName.NOTION
        assert result.access_token.get_secret_value() == "ntn_new_token"
        assert result.username == "user@example.com"
        assert result.access_token_expires_at is None
        assert result.refresh_token is None
        assert result.metadata["bot_id"] == "bot_123"
        assert result.metadata["workspace_id"] == "ws_456"


class TestNeedsRefresh:
    def test_needs_refresh_always_false(self):
        handler = _make_handler()
        credentials = _make_credentials()
        # Notion overrides needs_refresh to always return False
        assert handler.needs_refresh(credentials) is False


class TestRevokeTokens:
    @pytest.mark.asyncio
    async def test_revoke_tokens_returns_false(self):
        handler = _make_handler()
        credentials = _make_credentials()
        # Notion doesn't support token revocation
        result = await handler.revoke_tokens(credentials)
        assert result is False


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_tokens_returns_unchanged(self):
        handler = _make_handler()
        credentials = _make_credentials(access_token="original_token")
        # Notion doesn't support token refresh, returns credentials unchanged
        result = await handler._refresh_tokens(credentials)
        assert result.access_token.get_secret_value() == "original_token"
        assert result is credentials
