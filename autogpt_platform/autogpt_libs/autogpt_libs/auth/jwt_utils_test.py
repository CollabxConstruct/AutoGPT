"""Tests for JWT token parsing utilities.

This module tests:
- Successful parsing of valid JWT tokens
- Expired token handling
- Invalid token handling
- Wrong audience rejection
- Wrong algorithm rejection
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from autogpt_libs.auth.jwt_utils import parse_jwt_token

# Test constants
TEST_SECRET = "test-jwt-secret-key-for-unit-tests"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def mock_jwt_settings():
    """Patch auth settings for all tests in this module."""
    with patch("autogpt_libs.auth.jwt_utils.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = TEST_SECRET
        mock_settings.JWT_ALGORITHM = TEST_ALGORITHM
        yield mock_settings


class TestParseJwtToken:
    """Tests for the parse_jwt_token function."""

    def test_parse_valid_token(self):
        """A properly signed JWT with correct audience is decoded successfully."""
        payload = {
            "sub": "user-123",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)

        result = parse_jwt_token(token)

        assert result["sub"] == "user-123"
        assert result["role"] == "authenticated"

    def test_parse_expired_token(self):
        """An expired JWT raises ValueError with 'Token has expired'."""
        payload = {
            "sub": "user-456",
            "aud": "authenticated",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)

        with pytest.raises(ValueError, match="Token has expired"):
            parse_jwt_token(token)

    def test_parse_invalid_token(self):
        """A random non-JWT string raises ValueError with 'Invalid token'."""
        with pytest.raises(ValueError, match="Invalid token"):
            parse_jwt_token("this-is-not-a-jwt-token")

    def test_parse_wrong_audience(self):
        """A JWT with the wrong audience claim raises ValueError."""
        payload = {
            "sub": "user-789",
            "aud": "wrong-audience",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)

        with pytest.raises(ValueError, match="Invalid token"):
            parse_jwt_token(token)

    def test_parse_wrong_algorithm(self):
        """A JWT encoded with a different algorithm than configured raises ValueError."""
        payload = {
            "sub": "user-000",
            "aud": "authenticated",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        # Encode with HS384 while the decoder expects HS256
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS384")

        with pytest.raises(ValueError, match="Invalid token"):
            parse_jwt_token(token)
