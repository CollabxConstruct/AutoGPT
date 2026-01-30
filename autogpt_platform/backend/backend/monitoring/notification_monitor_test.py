"""Tests for notification_monitor module."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.monitoring.notification_monitor import (
    NotificationJobArgs,
    process_existing_batches,
    process_weekly_summary,
)


# ---------------------------------------------------------------------------
# NotificationJobArgs validation tests
# ---------------------------------------------------------------------------


class TestNotificationJobArgs:
    """Tests for NotificationJobArgs Pydantic model."""

    def test_notification_job_args_validation(self):
        """Valid arguments should parse correctly."""
        args = NotificationJobArgs(
            notification_types=["AGENT_RUN", "ZERO_BALANCE"],
            cron="0 * * * *",
        )
        assert len(args.notification_types) == 2
        assert args.cron == "0 * * * *"

    def test_notification_job_args_single_type(self):
        """A single notification type should parse correctly."""
        args = NotificationJobArgs(
            notification_types=["WEEKLY_SUMMARY"],
            cron="0 9 * * 1",
        )
        assert len(args.notification_types) == 1

    def test_notification_job_args_invalid(self):
        """Invalid arguments should raise ValidationError."""
        with pytest.raises(ValidationError):
            NotificationJobArgs(
                notification_types="not_a_list",  # type: ignore[arg-type]
                cron="0 * * * *",
            )

    def test_notification_job_args_missing_cron(self):
        """Missing cron field should raise ValidationError."""
        with pytest.raises(ValidationError):
            NotificationJobArgs(
                notification_types=["AGENT_RUN"],
                # cron is missing
            )

    def test_notification_job_args_missing_notification_types(self):
        """Missing notification_types field should raise ValidationError."""
        with pytest.raises(ValidationError):
            NotificationJobArgs(
                cron="0 * * * *",
                # notification_types is missing
            )


# ---------------------------------------------------------------------------
# process_existing_batches tests
# ---------------------------------------------------------------------------


class TestProcessExistingBatches:
    """Tests for the process_existing_batches function."""

    @patch("backend.monitoring.notification_monitor.get_notification_manager_client")
    def test_process_existing_batches_calls_client(self, mock_get_client):
        """Should call process_existing_batches on the notification client."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        process_existing_batches(
            notification_types=["AGENT_RUN", "ZERO_BALANCE"],
            cron="0 * * * *",
        )

        mock_client.process_existing_batches.assert_called_once()
        # Verify the notification types were passed
        call_args = mock_client.process_existing_batches.call_args
        notification_types = call_args[0][0]
        assert len(notification_types) == 2

    @patch("backend.monitoring.notification_monitor.get_notification_manager_client")
    def test_process_existing_batches_handles_error(self, mock_get_client):
        """Exception from the client should not propagate (caught internally)."""
        mock_client = MagicMock()
        mock_client.process_existing_batches.side_effect = RuntimeError("RabbitMQ down")
        mock_get_client.return_value = mock_client

        # Should not raise -- the function catches exceptions internally
        process_existing_batches(
            notification_types=["AGENT_RUN"],
            cron="0 * * * *",
        )

    @patch("backend.monitoring.notification_monitor.get_notification_manager_client")
    def test_process_existing_batches_invalid_kwargs_raises(self, mock_get_client):
        """Invalid kwargs should raise ValidationError before calling client."""
        with pytest.raises(ValidationError):
            process_existing_batches(
                notification_types="bad_value",  # not a list
                cron="0 * * * *",
            )


# ---------------------------------------------------------------------------
# process_weekly_summary tests
# ---------------------------------------------------------------------------


class TestProcessWeeklySummary:
    """Tests for the process_weekly_summary function."""

    @patch("backend.monitoring.notification_monitor.get_notification_manager_client")
    def test_process_weekly_summary_calls_client(self, mock_get_client):
        """Should call queue_weekly_summary on the notification client."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        process_weekly_summary()

        mock_client.queue_weekly_summary.assert_called_once()

    @patch("backend.monitoring.notification_monitor.get_notification_manager_client")
    def test_process_weekly_summary_handles_error(self, mock_get_client):
        """Exception from the client should not propagate (caught internally)."""
        mock_client = MagicMock()
        mock_client.queue_weekly_summary.side_effect = RuntimeError("Service down")
        mock_get_client.return_value = mock_client

        # Should not raise
        process_weekly_summary()
