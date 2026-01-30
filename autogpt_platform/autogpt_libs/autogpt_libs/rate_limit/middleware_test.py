"""Tests for the rate limit middleware.

This module tests:
- Non-API paths bypass rate limiting
- Missing Authorization header bypasses rate limiting
- Allowed requests pass through with rate limit headers
- Rate-limited requests return HTTP 429
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from autogpt_libs.rate_limit.middleware import rate_limit_middleware


def _make_request(path: str = "/api/v1/resource", auth_header: str = None):
    """Create a mock Request with the given path and optional Authorization header."""
    request = MagicMock()
    request.url = MagicMock()
    request.url.path = path
    headers = {}
    if auth_header is not None:
        headers["Authorization"] = auth_header
    request.headers = headers
    request.headers.get = lambda key, default=None: headers.get(key, default)
    return request


def _make_response():
    """Create a mock Response with a mutable headers dict."""
    response = MagicMock()
    response.headers = {}
    return response


class TestRateLimitMiddleware:
    """Tests for the rate_limit_middleware function."""

    @pytest.mark.asyncio
    async def test_non_api_path_bypasses_rate_limit(self):
        """Requests to non-/api paths are forwarded without rate limit checks."""
        request = _make_request(path="/health")
        expected_response = _make_response()
        call_next = AsyncMock(return_value=expected_response)

        with patch(
            "autogpt_libs.rate_limit.middleware.RateLimiter"
        ):
            result = await rate_limit_middleware(request, call_next)

        assert result is expected_response
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_no_auth_header_bypasses_rate_limit(self):
        """API requests without an Authorization header are forwarded without rate limit checks."""
        request = _make_request(path="/api/v1/data", auth_header=None)
        expected_response = _make_response()
        call_next = AsyncMock(return_value=expected_response)

        with patch(
            "autogpt_libs.rate_limit.middleware.RateLimiter"
        ):
            result = await rate_limit_middleware(request, call_next)

        assert result is expected_response
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_allowed_request_passes_through(self):
        """Under-limit requests pass through and the response includes rate limit headers."""
        request = _make_request(
            path="/api/v1/resource", auth_header="Bearer test-api-key"
        )
        expected_response = _make_response()
        call_next = AsyncMock(return_value=expected_response)

        mock_limiter = MagicMock()
        mock_limiter.check_rate_limit = AsyncMock(
            return_value=(True, 55, 1700000060)
        )
        mock_limiter.max_requests = 60

        with patch(
            "autogpt_libs.rate_limit.middleware.RateLimiter",
            return_value=mock_limiter,
        ):
            result = await rate_limit_middleware(request, call_next)

        assert result is expected_response
        call_next.assert_awaited_once_with(request)

        # Verify rate limit headers are set
        assert result.headers["X-RateLimit-Limit"] == "60"
        assert result.headers["X-RateLimit-Remaining"] == "55"
        assert result.headers["X-RateLimit-Reset"] == "1700000060"

        # Verify the Bearer prefix was stripped from the key
        mock_limiter.check_rate_limit.assert_awaited_once_with("test-api-key")

    @pytest.mark.asyncio
    async def test_rate_limited_request_returns_429(self):
        """Over-limit requests raise HTTPException with status code 429."""
        request = _make_request(
            path="/api/v1/resource", auth_header="Bearer rate-limited-key"
        )
        call_next = AsyncMock()

        mock_limiter = MagicMock()
        mock_limiter.check_rate_limit = AsyncMock(
            return_value=(False, 0, 1700000120)
        )
        mock_limiter.max_requests = 60

        with patch(
            "autogpt_libs.rate_limit.middleware.RateLimiter",
            return_value=mock_limiter,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_middleware(request, call_next)

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail

        # call_next should NOT have been called
        call_next.assert_not_awaited()
