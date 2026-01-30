import pydantic
import pytest

import backend.server.v2.AutoMod.models


def test_automod_request_valid() -> None:
    request = backend.server.v2.AutoMod.models.AutoModRequest(
        type="text",
        content="Hello, this is a test message.",
        metadata={"source": "user_input"},
    )
    assert request.type == "text"
    assert request.content == "Hello, this is a test message."
    assert request.metadata == {"source": "user_input"}


def test_automod_request_without_metadata() -> None:
    request = backend.server.v2.AutoMod.models.AutoModRequest(
        type="image",
        content="https://example.com/image.png",
    )
    assert request.type == "image"
    assert request.content == "https://example.com/image.png"
    assert request.metadata is None


def test_automod_response_approved() -> None:
    response = backend.server.v2.AutoMod.models.AutoModResponse(
        success=True,
        status="approved",
        moderation_results=[],
    )
    assert response.success is True
    assert response.status == "approved"
    assert response.moderation_results == []


def test_automod_response_rejected() -> None:
    result = backend.server.v2.AutoMod.models.ModerationResult(
        decision="rejected",
        reason="Contains prohibited content",
    )
    response = backend.server.v2.AutoMod.models.AutoModResponse(
        success=True,
        status="rejected",
        moderation_results=[result],
    )
    assert response.success is True
    assert response.status == "rejected"
    assert len(response.moderation_results) == 1
    assert response.moderation_results[0].decision == "rejected"
    assert response.moderation_results[0].reason == "Contains prohibited content"


def test_moderation_config_defaults() -> None:
    config = backend.server.v2.AutoMod.models.ModerationConfig(
        api_key="test-api-key",
    )
    assert config.enabled is True
    assert config.api_url == ""
    assert config.api_key == "test-api-key"
    assert config.timeout == 30
    assert config.retry_attempts == 3
    assert config.retry_delay == 1.0
    assert config.fail_open is False
    assert config.moderate_inputs is True
    assert config.moderate_outputs is True


def test_moderation_config_custom() -> None:
    config = backend.server.v2.AutoMod.models.ModerationConfig(
        enabled=False,
        api_url="https://automod.example.com",
        api_key="custom-key",
        timeout=60,
        retry_attempts=5,
        retry_delay=2.5,
        fail_open=True,
        moderate_inputs=False,
        moderate_outputs=False,
    )
    assert config.enabled is False
    assert config.api_url == "https://automod.example.com"
    assert config.api_key == "custom-key"
    assert config.timeout == 60
    assert config.retry_attempts == 5
    assert config.retry_delay == 2.5
    assert config.fail_open is True
    assert config.moderate_inputs is False
    assert config.moderate_outputs is False
