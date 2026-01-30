import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from backend.data.model import OAuth2Credentials
from backend.integrations.oauth.github import GitHubOAuthHandler
from backend.integrations.providers import ProviderName


def _make_handler() -> GitHubOAuthHandler:
    return GitHubOAuthHandler(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost/callback",
    )


def _make_credentials(
    access_token: str = "test_access_token",
    refresh_token: str | None = None,
    access_token_expires_at: int | None = None,
) -> OAuth2Credentials:
    return OAuth2Credentials(
        provider=ProviderName.GITHUB,
        access_token=SecretStr(access_token),
        refresh_token=SecretStr(refresh_token) if refresh_token else None,
        access_token_expires_at=access_token_expires_at,
        scopes=["repo"],
    )


class TestGetLoginUrl:
    def test_get_login_url(self):
        handler = _make_handler()
        url = handler.get_login_url(scopes=["repo"], state="test_state", code_challenge=None)
        assert "client_id=test_client_id" in url
        assert "redirect_uri=" in url
        assert "scope=repo" in url
        assert "state=test_state" in url
        assert url.startswith("https://github.com/login/oauth/authorize?")

    def test_get_login_url_scopes(self):
        handler = _make_handler()
        url = handler.get_login_url(
            scopes=["repo", "user", "gist"], state="s", code_challenge=None
        )
        # Scopes should be space-separated (URL-encoded as +)
        assert "scope=repo+user+gist" in url or "scope=repo%20user%20gist" in url


class TestExchangeCodeForTokens:
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens(self):
        handler = _make_handler()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "gho_new_token",
            "token_type": "bearer",
            "scope": "repo,user",
        }

        mock_user_response = MagicMock()
        mock_user_response.ok = True
        mock_user_response.json.return_value = {"login": "testuser"}

        with patch(
            "backend.integrations.oauth.github.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            mock_requests_instance.get = AsyncMock(return_value=mock_user_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler.exchange_code_for_tokens(
                code="test_code", scopes=["repo"], code_verifier=None
            )

        assert result.provider == ProviderName.GITHUB
        assert result.access_token.get_secret_value() == "gho_new_token"
        assert result.username == "testuser"


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_tokens_no_refresh_token(self):
        handler = _make_handler()
        credentials = _make_credentials(refresh_token=None)
        result = await handler._refresh_tokens(credentials)
        # When no refresh token, returns credentials unchanged
        assert result.access_token.get_secret_value() == "test_access_token"

    @pytest.mark.asyncio
    async def test_refresh_tokens_with_refresh_token(self):
        handler = _make_handler()
        credentials = _make_credentials(refresh_token="test_refresh_token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "gho_refreshed_token",
            "refresh_token": "gho_new_refresh",
            "token_type": "bearer",
            "scope": "repo",
            "expires_in": 28800,
            "refresh_token_expires_in": 15897600,
        }

        mock_user_response = MagicMock()
        mock_user_response.ok = True
        mock_user_response.json.return_value = {"login": "testuser"}

        with patch(
            "backend.integrations.oauth.github.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            mock_requests_instance.get = AsyncMock(return_value=mock_user_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler._refresh_tokens(credentials)

        assert result.access_token.get_secret_value() == "gho_refreshed_token"
        assert result.refresh_token.get_secret_value() == "gho_new_refresh"
        # Verify _request_tokens was called with grant_type=refresh_token
        call_args = mock_requests_instance.post.call_args
        assert call_args.kwargs.get("data", {}).get("grant_type") == "refresh_token" or (
            "grant_type" in (call_args[1].get("data", {}) if len(call_args) > 1 else {})
        )


class TestRevokeTokens:
    @pytest.mark.asyncio
    async def test_revoke_tokens(self):
        handler = _make_handler()
        credentials = _make_credentials(access_token="token_to_revoke")

        mock_response = MagicMock()
        mock_response.ok = True

        with patch(
            "backend.integrations.oauth.github.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.delete = AsyncMock(return_value=mock_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler.revoke_tokens(credentials)

        assert result is True
        mock_requests_instance.delete.assert_called_once()
        call_args = mock_requests_instance.delete.call_args
        # Verify the URL contains the client_id
        assert "test_client_id" in call_args.kwargs.get("url", call_args[0][0] if call_args[0] else "")
