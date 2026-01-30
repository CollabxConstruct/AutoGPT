"""Tests for notifications module utility functions."""

from unittest.mock import patch

import pytest
from prisma.enums import NotificationType

from backend.notifications.notifications import (
    create_notification_config,
    get_routing_key,
)


# ---------------------------------------------------------------------------
# get_routing_key tests
# ---------------------------------------------------------------------------


class TestGetRoutingKey:
    """Tests for the get_routing_key function."""

    def test_get_routing_key_returns_string(self):
        """The routing key should always be a string."""
        key = get_routing_key(NotificationType.AGENT_RUN)
        assert isinstance(key, str)

    def test_get_routing_key_contains_event_type(self):
        """The routing key should contain the event type value."""
        for nt in NotificationType:
            key = get_routing_key(nt)
            assert nt.value in key, (
                f"Routing key '{key}' does not contain event type value '{nt.value}'"
            )

    def test_get_routing_key_agent_run_is_batch(self):
        """AGENT_RUN should use batch routing."""
        key = get_routing_key(NotificationType.AGENT_RUN)
        assert key == f"notification.batch.{NotificationType.AGENT_RUN.value}"

    def test_get_routing_key_zero_balance_is_backoff(self):
        """ZERO_BALANCE should use backoff routing."""
        key = get_routing_key(NotificationType.ZERO_BALANCE)
        assert key == f"notification.backoff.{NotificationType.ZERO_BALANCE.value}"

    def test_get_routing_key_low_balance_is_immediate(self):
        """LOW_BALANCE should use immediate routing."""
        key = get_routing_key(NotificationType.LOW_BALANCE)
        assert key == f"notification.immediate.{NotificationType.LOW_BALANCE.value}"

    def test_get_routing_key_refund_request_is_admin(self):
        """REFUND_REQUEST should use admin routing."""
        key = get_routing_key(NotificationType.REFUND_REQUEST)
        assert key == f"notification.admin.{NotificationType.REFUND_REQUEST.value}"

    def test_get_routing_key_weekly_summary_is_summary(self):
        """WEEKLY_SUMMARY should use summary routing."""
        key = get_routing_key(NotificationType.WEEKLY_SUMMARY)
        assert key == f"notification.summary.{NotificationType.WEEKLY_SUMMARY.value}"

    def test_get_routing_key_daily_summary_is_summary(self):
        """DAILY_SUMMARY should use summary routing."""
        key = get_routing_key(NotificationType.DAILY_SUMMARY)
        assert key == f"notification.summary.{NotificationType.DAILY_SUMMARY.value}"

    def test_get_routing_key_prefix(self):
        """All routing keys should start with 'notification.'."""
        for nt in NotificationType:
            key = get_routing_key(nt)
            assert key.startswith("notification."), (
                f"Routing key '{key}' does not start with 'notification.'"
            )


# ---------------------------------------------------------------------------
# create_notification_config tests
# ---------------------------------------------------------------------------


class TestCreateNotificationConfig:
    """Tests for the create_notification_config function."""

    def test_create_notification_config_has_queues(self):
        """Config should have exactly 5 queues."""
        config = create_notification_config()
        assert len(config.queues) == 5

    def test_create_notification_config_queue_names(self):
        """Queue names should include immediate, admin, summary, batch, and failed."""
        config = create_notification_config()
        queue_names = {q.name for q in config.queues}

        expected_names = {
            "immediate_notifications",
            "admin_notifications",
            "summary_notifications",
            "batch_notifications",
            "failed_notifications",
        }
        assert queue_names == expected_names

    def test_create_notification_config_exchanges(self):
        """Config should have notification and dead_letter exchanges."""
        config = create_notification_config()
        exchange_names = {e.name for e in config.exchanges}

        assert "notifications" in exchange_names
        assert "dead_letter" in exchange_names

    def test_create_notification_config_exchange_count(self):
        """Config should have exactly 2 exchanges."""
        config = create_notification_config()
        assert len(config.exchanges) == 2

    def test_create_notification_config_dead_letter_routing(self):
        """Non-failed queues should have dead letter exchange arguments."""
        config = create_notification_config()
        non_failed_queues = [q for q in config.queues if q.name != "failed_notifications"]

        for queue in non_failed_queues:
            assert queue.arguments is not None, (
                f"Queue '{queue.name}' should have dead letter arguments"
            )
            assert "x-dead-letter-exchange" in queue.arguments, (
                f"Queue '{queue.name}' missing x-dead-letter-exchange"
            )
            assert queue.arguments["x-dead-letter-exchange"] == "dead_letter", (
                f"Queue '{queue.name}' has wrong dead letter exchange"
            )

    def test_create_notification_config_routing_keys(self):
        """Each queue should have a routing key matching its purpose."""
        config = create_notification_config()
        routing_keys = {q.name: q.routing_key for q in config.queues}

        assert "notification.immediate.#" == routing_keys["immediate_notifications"]
        assert "notification.admin.#" == routing_keys["admin_notifications"]
        assert "notification.summary.#" == routing_keys["summary_notifications"]
        assert "notification.batch.#" == routing_keys["batch_notifications"]
        assert "failed.#" == routing_keys["failed_notifications"]

    def test_create_notification_config_returns_rabbitmq_config(self):
        """Should return a RabbitMQConfig instance."""
        from backend.data.rabbitmq import RabbitMQConfig

        config = create_notification_config()
        assert isinstance(config, RabbitMQConfig)
