import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from backend.data.model import OAuth2Credentials
from backend.integrations.oauth.twitter import TwitterOAuthHandler
from backend.integrations.providers import ProviderName


def _make_handler() -> TwitterOAuthHandler:
    return TwitterOAuthHandler(
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
        provider=ProviderName.TWITTER,
        access_token=SecretStr(access_token),
        refresh_token=SecretStr(refresh_token) if refresh_token else None,
        access_token_expires_at=access_token_expires_at,
        scopes=["tweet.read", "users.read"],
    )


class TestGetLoginUrl:
    def test_get_login_url_requires_code_challenge(self):
        handler = _make_handler()
        with pytest.raises(ValueError, match="code_challenge is required"):
            handler.get_login_url(
                scopes=["tweet.read"], state="test_state", code_challenge=None
            )

    def test_get_login_url_format(self):
        handler = _make_handler()
        url = handler.get_login_url(
            scopes=["tweet.read"],
            state="test_state",
            code_challenge="test_challenge_value",
        )
        assert "response_type=code" in url
        assert "code_challenge_method=S256" in url
        assert "code_challenge=test_challenge_value" in url
        assert "client_id=test_client_id" in url
        assert "state=test_state" in url
        assert url.startswith("https://twitter.com/i/oauth2/authorize?")


class TestExchangeCodeForTokens:
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens(self):
        handler = _make_handler()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "tw_new_token",
            "refresh_token": "tw_refresh",
            "token_type": "bearer",
            "expires_in": 7200,
        }

        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "data": {"username": "twitteruser"}
        }

        with patch(
            "backend.integrations.oauth.twitter.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            mock_requests_instance.get = AsyncMock(return_value=mock_user_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler.exchange_code_for_tokens(
                code="test_code",
                scopes=["tweet.read", "users.read"],
                code_verifier="test_verifier",
            )

        assert result.provider == ProviderName.TWITTER
        assert result.access_token.get_secret_value() == "tw_new_token"
        assert result.refresh_token.get_secret_value() == "tw_refresh"
        assert result.username == "twitteruser"
        assert result.access_token_expires_at is not None


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_tokens_no_refresh_token(self):
        handler = _make_handler()
        credentials = _make_credentials(refresh_token=None)
        with pytest.raises(ValueError, match="No refresh token available"):
            await handler._refresh_tokens(credentials)

    @pytest.mark.asyncio
    async def test_refresh_tokens_with_refresh_token(self):
        handler = _make_handler()
        credentials = _make_credentials(
            access_token="old_token",
            refresh_token="existing_refresh",
            access_token_expires_at=int(time.time()) + 100,
        )

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "tw_refreshed_token",
            "refresh_token": "tw_new_refresh",
            "token_type": "bearer",
            "expires_in": 7200,
        }

        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "data": {"username": "twitteruser"}
        }

        with patch(
            "backend.integrations.oauth.twitter.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            mock_requests_instance.get = AsyncMock(return_value=mock_user_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler._refresh_tokens(credentials)

        assert result.access_token.get_secret_value() == "tw_refreshed_token"
        assert result.refresh_token.get_secret_value() == "tw_new_refresh"
        mock_requests_instance.post.assert_called_once()


class TestRevokeTokens:
    @pytest.mark.asyncio
    async def test_revoke_tokens(self):
        handler = _make_handler()
        credentials = _make_credentials(access_token="token_to_revoke")

        mock_response = MagicMock()
        mock_response.ok = True

        with patch(
            "backend.integrations.oauth.twitter.Requests"
        ) as MockRequests:
            mock_requests_instance = MagicMock()
            mock_requests_instance.post = AsyncMock(return_value=mock_response)
            MockRequests.return_value = mock_requests_instance

            result = await handler.revoke_tokens(credentials)

        assert result is True
        mock_requests_instance.post.assert_called_once()
        call_args = mock_requests_instance.post.call_args
        # Verify the revoke URL was used
        called_url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
        assert called_url == "https://api.x.com/2/oauth2/revoke"
