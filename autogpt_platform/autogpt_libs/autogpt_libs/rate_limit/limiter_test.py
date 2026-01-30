"""Tests for the rate limiter.

This module tests:
- Rate limit checks under, at, and over the limit
- Redis key format used for rate limiting
- Window duration configuration
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from autogpt_libs.rate_limit.limiter import RateLimiter


@pytest.fixture
def mock_redis():
    """Create a mock Redis client and patch the Redis constructor."""
    with patch("autogpt_libs.rate_limit.limiter.Redis") as mock_redis_cls:
        mock_instance = MagicMock()
        mock_redis_cls.return_value = mock_instance
        yield mock_instance


def _create_limiter(mock_redis_fixture, requests_per_minute=10):
    """Helper to create a RateLimiter with mocked Redis."""
    limiter = RateLimiter(
        redis_host="localhost",
        redis_port="6379",
        redis_password="testpass",
        requests_per_minute=requests_per_minute,
    )
    # Replace the redis instance with our mock
    limiter.redis = mock_redis_fixture
    return limiter


class TestCheckRateLimit:
    """Tests for the check_rate_limit method."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, mock_redis):
        """When under the limit, returns (True, remaining > 0, reset_time)."""
        limiter = _create_limiter(mock_redis, requests_per_minute=10)

        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # Simulate: zremrangebyscore result, zadd result, zcount=5, expire result
        mock_pipe.execute.return_value = [0, 1, 5, True]

        is_allowed, remaining, reset_time = await limiter.check_rate_limit(
            "test-key-1"
        )

        assert is_allowed is True
        assert remaining == 5  # 10 - 5
        assert reset_time > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(self, mock_redis):
        """When exactly at the limit, returns (True, 0, reset_time)."""
        limiter = _create_limiter(mock_redis, requests_per_minute=10)

        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # request_count == max_requests (10 <= 10 is True)
        mock_pipe.execute.return_value = [0, 1, 10, True]

        is_allowed, remaining, reset_time = await limiter.check_rate_limit(
            "test-key-2"
        )

        assert is_allowed is True
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_over_limit(self, mock_redis):
        """When over the limit, returns (False, 0, reset_time)."""
        limiter = _create_limiter(mock_redis, requests_per_minute=10)

        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # request_count=11 > max_requests=10
        mock_pipe.execute.return_value = [0, 1, 11, True]

        is_allowed, remaining, reset_time = await limiter.check_rate_limit(
            "test-key-3"
        )

        assert is_allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_rate_limit_key_format(self, mock_redis):
        """The Redis key follows the pattern 'ratelimit:{api_key_id}:1min'."""
        limiter = _create_limiter(mock_redis, requests_per_minute=10)

        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 1, 1, True]

        await limiter.check_rate_limit("my-api-key-id")

        # Verify the key pattern used in pipeline calls
        calls = mock_pipe.zremrangebyscore.call_args_list
        assert len(calls) == 1
        key_arg = calls[0][0][0]
        assert key_arg == "ratelimit:my-api-key-id:1min"

    def test_rate_limit_window(self, mock_redis):
        """The rate limit window is 60 seconds."""
        limiter = _create_limiter(mock_redis)
        assert limiter.window == 60

    @pytest.mark.asyncio
    async def test_rate_limit_reset_time(self, mock_redis):
        """The reset_time is approximately now + 60 seconds."""
        limiter = _create_limiter(mock_redis, requests_per_minute=10)

        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 1, 1, True]

        before = int(time.time() + 60)
        _, _, reset_time = await limiter.check_rate_limit("test-key")
        after = int(time.time() + 60)

        assert before <= reset_time <= after
