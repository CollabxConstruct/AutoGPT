import pydantic
import pytest

import backend.server.v2.turnstile.models


def test_verify_request_required_fields() -> None:
    """Token is a required field on TurnstileVerifyRequest."""
    request = backend.server.v2.turnstile.models.TurnstileVerifyRequest(
        token="test-token-abc123",
    )
    assert request.token == "test-token-abc123"


def test_verify_request_missing_token() -> None:
    """TurnstileVerifyRequest should fail without a token."""
    with pytest.raises(pydantic.ValidationError):
        backend.server.v2.turnstile.models.TurnstileVerifyRequest()  # type: ignore[call-arg]


def test_verify_request_optional_fields() -> None:
    """Action is an optional field that defaults to None."""
    request_without_action = backend.server.v2.turnstile.models.TurnstileVerifyRequest(
        token="test-token",
    )
    assert request_without_action.action is None

    request_with_action = backend.server.v2.turnstile.models.TurnstileVerifyRequest(
        token="test-token",
        action="login",
    )
    assert request_with_action.action == "login"


def test_verify_response_success() -> None:
    """Successful verification response with all fields populated."""
    response = backend.server.v2.turnstile.models.TurnstileVerifyResponse(
        success=True,
        error=None,
        challenge_timestamp="2023-01-01T00:00:00Z",
        hostname="example.com",
        action="login",
    )
    assert response.success is True
    assert response.error is None
    assert response.challenge_timestamp == "2023-01-01T00:00:00Z"
    assert response.hostname == "example.com"
    assert response.action == "login"


def test_verify_response_failure() -> None:
    """Failed verification response with an error message."""
    response = backend.server.v2.turnstile.models.TurnstileVerifyResponse(
        success=False,
        error="invalid-input-response",
    )
    assert response.success is False
    assert response.error == "invalid-input-response"
    assert response.challenge_timestamp is None
    assert response.hostname is None
    assert response.action is None


def test_verify_response_defaults() -> None:
    """Optional fields on TurnstileVerifyResponse default to None."""
    response = backend.server.v2.turnstile.models.TurnstileVerifyResponse(
        success=True,
    )
    assert response.success is True
    assert response.error is None
    assert response.challenge_timestamp is None
    assert response.hostname is None
    assert response.action is None
