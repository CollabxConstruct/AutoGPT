"""Tests for late_execution_monitor module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.monitoring.late_execution_monitor import LateExecutionMonitor


@pytest.fixture()
def _mock_clients():
    """Patch the client factory functions used by LateExecutionMonitor."""
    with (
        patch(
            "backend.monitoring.late_execution_monitor.get_database_manager_client"
        ) as mock_db,
        patch(
            "backend.monitoring.late_execution_monitor.get_notification_manager_client"
        ) as mock_notif,
        patch(
            "backend.monitoring.late_execution_monitor.sentry_capture_error"
        ) as mock_sentry,
        patch("backend.monitoring.late_execution_monitor.Config") as mock_config_cls,
    ):
        mock_cfg = MagicMock()
        mock_cfg.execution_late_notification_checkrange_secs = 3600
        mock_cfg.execution_late_notification_threshold_secs = 300
        mock_config_cls.return_value = mock_cfg

        yield {
            "db": mock_db,
            "notif": mock_notif,
            "sentry": mock_sentry,
            "config": mock_cfg,
        }


def _make_execution(
    exec_id: str = "exec-1",
    graph_id: str = "graph-1",
    graph_version: int = 1,
    user_id: str = "user-1",
    status: str = "QUEUED",
    started_at: datetime | None = None,
):
    """Create a mock execution object matching GraphExecutionMeta fields."""
    mock_exec = MagicMock()
    mock_exec.id = exec_id
    mock_exec.graph_id = graph_id
    mock_exec.graph_version = graph_version
    mock_exec.user_id = user_id
    mock_exec.status = status
    mock_exec.started_at = started_at or datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return mock_exec


class TestLateExecutionMonitor:
    """Tests for LateExecutionMonitor.check_late_executions."""

    def test_no_late_executions(self, _mock_clients):
        """Should return 'No late executions detected.' when no executions are late."""
        db_client = _mock_clients["db"].return_value
        db_client.get_graph_executions.return_value = []

        monitor = LateExecutionMonitor()
        result = monitor.check_late_executions()

        assert result == "No late executions detected."
        # Notification should NOT be sent
        _mock_clients["notif"].return_value.discord_system_alert.assert_not_called()

    def test_queued_late_executions(self, _mock_clients):
        """Should detect queued late executions and send an alert."""
        queued_exec = _make_execution(
            exec_id="exec-q1",
            status="QUEUED",
            user_id="user-1",
        )

        db_client = _mock_clients["db"].return_value
        # First call returns queued executions, second returns running (empty)
        db_client.get_graph_executions.side_effect = [
            [queued_exec],  # queued late
            [],  # running late
        ]

        monitor = LateExecutionMonitor()
        result = monitor.check_late_executions()

        assert "late executions detected" in result.lower() or "Late executions" in result
        assert "1 QUEUED" in result
        # Discord alert should be sent
        _mock_clients["notif"].return_value.discord_system_alert.assert_called_once()
        # Sentry should capture the error
        _mock_clients["sentry"].assert_called_once()

    def test_running_late_executions(self, _mock_clients):
        """Should detect running executions stuck for over 24 hours."""
        running_exec = _make_execution(
            exec_id="exec-r1",
            status="RUNNING",
            user_id="user-2",
        )

        db_client = _mock_clients["db"].return_value
        # First call returns queued (empty), second returns running late
        db_client.get_graph_executions.side_effect = [
            [],  # queued late
            [running_exec],  # running late
        ]

        monitor = LateExecutionMonitor()
        result = monitor.check_late_executions()

        assert "Late executions detected" in result or "late executions" in result.lower()
        assert "1 RUNNING" in result
        _mock_clients["notif"].return_value.discord_system_alert.assert_called_once()

    def test_truncation(self, _mock_clients):
        """More than 5 executions should be truncated in the output."""
        executions = [
            _make_execution(
                exec_id=f"exec-{i}",
                user_id=f"user-{i}",
                status="QUEUED",
                started_at=datetime(2024, 1, 1, i, 0, 0, tzinfo=timezone.utc),
            )
            for i in range(8)
        ]

        db_client = _mock_clients["db"].return_value
        db_client.get_graph_executions.side_effect = [
            executions,  # queued late
            [],  # running late
        ]

        monitor = LateExecutionMonitor()
        result = monitor.check_late_executions()

        # Should mention the total count
        assert "8 total late executions" in result
        # Should mention truncation
        assert "Showing first 5 of 8" in result
        # Discord alert should be sent
        _mock_clients["notif"].return_value.discord_system_alert.assert_called_once()

    def test_mixed_queued_and_running(self, _mock_clients):
        """Should handle both queued and running late executions."""
        queued_execs = [
            _make_execution(exec_id="exec-q1", status="QUEUED", user_id="user-1"),
            _make_execution(exec_id="exec-q2", status="QUEUED", user_id="user-2"),
        ]
        running_execs = [
            _make_execution(exec_id="exec-r1", status="RUNNING", user_id="user-3"),
        ]

        db_client = _mock_clients["db"].return_value
        db_client.get_graph_executions.side_effect = [
            queued_execs,
            running_execs,
        ]

        monitor = LateExecutionMonitor()
        result = monitor.check_late_executions()

        assert "3 total late executions" in result
        assert "2 QUEUED" in result
        assert "1 RUNNING" in result
