"""Tests for the auth middleware and APIKeyValidator.

This module tests:
- auth_middleware behavior when auth is enabled/disabled
- JWT token validation through the middleware
- APIKeyValidator with default and custom validators
- API key storage in request state
- get_dependency method
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from autogpt_libs.auth.middleware import APIKeyValidator, auth_middleware


class TestAuthMiddleware:
    """Tests for the auth_middleware function."""

    @pytest.mark.asyncio
    async def test_auth_middleware_disabled(self):
        """When ENABLE_AUTH is False, the middleware returns an empty dict."""
        request = MagicMock()
        with patch(
            "autogpt_libs.auth.middleware.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AUTH = False
            result = await auth_middleware(request)
            assert result == {}

    @pytest.mark.asyncio
    async def test_auth_middleware_valid_token(self):
        """With a valid token, the middleware decodes it and sets request.state.user."""
        request = MagicMock()
        request.state = MagicMock()
        expected_payload = {"sub": "user-123", "role": "authenticated"}

        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.jwt.token"

        with (
            patch(
                "autogpt_libs.auth.middleware.settings"
            ) as mock_settings,
            patch(
                "autogpt_libs.auth.middleware.parse_jwt_token",
                return_value=expected_payload,
            ) as mock_parse,
            patch(
                "autogpt_libs.auth.middleware.HTTPBearer"
            ) as mock_bearer_cls,
        ):
            mock_settings.ENABLE_AUTH = True
            mock_bearer_instance = AsyncMock(return_value=mock_credentials)
            mock_bearer_cls.return_value = mock_bearer_instance

            result = await auth_middleware(request)

            assert result == expected_payload
            mock_parse.assert_called_once_with("valid.jwt.token")
            assert request.state.user == expected_payload

    @pytest.mark.asyncio
    async def test_auth_middleware_invalid_token(self):
        """When parse_jwt_token raises ValueError, middleware raises HTTPException 401."""
        request = MagicMock()
        request.state = MagicMock()

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.jwt.token"

        with (
            patch(
                "autogpt_libs.auth.middleware.settings"
            ) as mock_settings,
            patch(
                "autogpt_libs.auth.middleware.parse_jwt_token",
                side_effect=ValueError("Invalid token: bad signature"),
            ),
            patch(
                "autogpt_libs.auth.middleware.HTTPBearer"
            ) as mock_bearer_cls,
        ):
            mock_settings.ENABLE_AUTH = True
            mock_bearer_instance = AsyncMock(return_value=mock_credentials)
            mock_bearer_cls.return_value = mock_bearer_instance

            with pytest.raises(HTTPException) as exc_info:
                await auth_middleware(request)
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail


class TestAPIKeyValidator:
    """Tests for the APIKeyValidator class."""

    @pytest.mark.asyncio
    async def test_api_key_validator_valid_key(self):
        """With the correct expected_token, the validator returns True."""
        validator = APIKeyValidator(
            header_name="X-API-Key",
            expected_token="secret-token-123",
        )
        request = MagicMock()
        request.state = MagicMock()

        result = await validator(request, "secret-token-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_api_key_validator_invalid_key(self):
        """With a wrong key, the validator raises HTTPException."""
        validator = APIKeyValidator(
            header_name="X-API-Key",
            expected_token="secret-token-123",
        )
        request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await validator(request, "wrong-key")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"

    @pytest.mark.asyncio
    async def test_api_key_validator_missing_key(self):
        """With None as the API key, the validator raises HTTPException."""
        validator = APIKeyValidator(
            header_name="X-API-Key",
            expected_token="secret-token-123",
        )
        request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await validator(request, None)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Missing API key"

    @pytest.mark.asyncio
    async def test_api_key_validator_no_expected_token(self):
        """When no expected_token is set, default_validator raises ValueError."""
        validator = APIKeyValidator(
            header_name="X-API-Key",
        )

        with pytest.raises(ValueError, match="Expected Token Required"):
            await validator.default_validator("any-key")

    @pytest.mark.asyncio
    async def test_api_key_validator_custom_sync_validator(self):
        """A synchronous custom validate_fn is invoked correctly."""

        def sync_validator(api_key: str) -> bool:
            return api_key == "sync-valid-key"

        validator = APIKeyValidator(
            header_name="X-API-Key",
            validate_fn=sync_validator,
        )
        request = MagicMock()
        request.state = MagicMock()

        result = await validator(request, "sync-valid-key")
        assert result is True

        with pytest.raises(HTTPException) as exc_info:
            await validator(request, "bad-key")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_validator_custom_async_validator(self):
        """An asynchronous custom validate_fn is invoked correctly."""

        async def async_validator(api_key: str) -> bool:
            return api_key == "async-valid-key"

        validator = APIKeyValidator(
            header_name="X-API-Key",
            validate_fn=async_validator,
        )
        request = MagicMock()
        request.state = MagicMock()

        result = await validator(request, "async-valid-key")
        assert result is True

        with pytest.raises(HTTPException) as exc_info:
            await validator(request, "bad-key")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_validator_result_stored_in_state(self):
        """When a custom validator returns a non-boolean object, it is stored in request.state."""

        api_key_record = {"id": "key-42", "name": "test-key", "active": True}

        async def db_validator(api_key: str):
            if api_key == "valid-db-key":
                return api_key_record
            return None

        validator = APIKeyValidator(
            header_name="X-API-Key",
            validate_fn=db_validator,
        )
        request = MagicMock()
        request.state = MagicMock()

        result = await validator(request, "valid-db-key")
        assert result == api_key_record
        assert request.state.api_key == api_key_record

    def test_get_dependency_returns_callable(self):
        """get_dependency returns a callable with the correct __name__."""
        validator = APIKeyValidator(
            header_name="X-Custom-Header",
            expected_token="token",
        )
        dependency = validator.get_dependency()
        assert callable(dependency)
        assert dependency.__name__ == "validate_X-Custom-Header"
