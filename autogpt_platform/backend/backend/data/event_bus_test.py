"""Tests for event bus serialization/deserialization logic."""

from unittest.mock import patch, MagicMock

import pytest
from pydantic import BaseModel

from backend.data.event_bus import BaseRedisEventBus


# ---------------------------------------------------------------------------
# Test fixtures: concrete subclass and simple event model
# ---------------------------------------------------------------------------

class SimpleEvent(BaseModel):
    """A simple Pydantic model used as the event type in tests."""
    event_type: str = "test"
    message: str = ""


class ConcreteEventBus(BaseRedisEventBus[SimpleEvent]):
    """Non-abstract subclass of BaseRedisEventBus for testing."""
    Model = SimpleEvent

    @property
    def event_bus_name(self) -> str:
        return "test_bus"


@pytest.fixture
def bus():
    return ConcreteEventBus()


# ---------------------------------------------------------------------------
# _serialize_message tests
# ---------------------------------------------------------------------------

class TestSerializeMessage:
    def test_serialize_message_normal(self, bus):
        """A message below the size limit serializes normally."""
        event = SimpleEvent(event_type="update", message="hello")
        # Use a high size limit so the message is always under it
        with patch.object(
            type(bus),
            "_serialize_message",
            wraps=bus._serialize_message,
        ):
            mock_config = MagicMock()
            mock_config.max_message_size_limit = 16 * 1024 * 1024  # 16 MB
            with patch("backend.data.event_bus.config", mock_config):
                message, channel = bus._serialize_message(event, "chan1")

        assert isinstance(message, str)
        assert '"payload"' in message
        assert '"hello"' in message
        assert channel == "test_bus/chan1"

    def test_serialize_message_too_large(self, bus):
        """A message exceeding max_message_size_limit is replaced with an error payload."""
        # Create a message that will exceed a very small size limit
        event = SimpleEvent(
            event_type="big_update",
            message="x" * 500,
        )
        mock_config = MagicMock()
        mock_config.max_message_size_limit = 10  # Extremely small limit
        with patch("backend.data.event_bus.config", mock_config):
            message, channel = bus._serialize_message(event, "chan2")

        assert "error_comms_update" in message
        assert "Payload too large" in message
        assert "original_size_bytes" in message
        assert channel == "test_bus/chan2"


# ---------------------------------------------------------------------------
# _deserialize_message tests
# ---------------------------------------------------------------------------

class TestDeserializeMessage:
    def _make_serialized_payload(self, bus, event: SimpleEvent) -> str:
        """Helper: produce the JSON string for a wrapped event."""
        from backend.util import json as json_util

        wrapper = bus.Message(payload=event)
        return json_util.dumps(wrapper, ensure_ascii=False, separators=(",", ":"))

    def test_deserialize_message_valid(self, bus):
        """A valid 'message' type with correct JSON deserializes to the event model."""
        event = SimpleEvent(event_type="info", message="world")
        data = self._make_serialized_payload(bus, event)
        msg = {"type": "message", "data": data}

        result = bus._deserialize_message(msg, "chan1")

        assert result is not None
        assert isinstance(result, SimpleEvent)
        assert result.event_type == "info"
        assert result.message == "world"

    def test_deserialize_message_wrong_type(self, bus):
        """A message with type != 'message' (e.g. 'subscribe') returns None."""
        event = SimpleEvent(event_type="info", message="world")
        data = self._make_serialized_payload(bus, event)
        msg = {"type": "subscribe", "data": data}

        result = bus._deserialize_message(msg, "chan1")
        assert result is None

    def test_deserialize_message_invalid_json(self, bus):
        """Invalid JSON data returns None instead of raising."""
        msg = {"type": "message", "data": "this is {not valid json!!!"}

        result = bus._deserialize_message(msg, "chan1")
        assert result is None

    def test_deserialize_message_pattern_channel(self, bus):
        """When channel_key contains '*', expects 'pmessage' type."""
        event = SimpleEvent(event_type="glob", message="pattern")
        data = self._make_serialized_payload(bus, event)

        # pmessage type with wildcard channel should work
        msg_ok = {"type": "pmessage", "data": data}
        result = bus._deserialize_message(msg_ok, "chan/*")
        assert result is not None
        assert result.event_type == "glob"

        # 'message' type with wildcard channel should NOT match
        msg_bad = {"type": "message", "data": data}
        result = bus._deserialize_message(msg_bad, "chan/*")
        assert result is None
