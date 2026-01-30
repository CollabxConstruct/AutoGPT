"""Tests for block_error_monitor module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.monitoring.block_error_monitor import (
    BlockErrorMonitor,
    BlockStatsWithSamples,
)


# ---------------------------------------------------------------------------
# BlockStatsWithSamples tests
# ---------------------------------------------------------------------------


class TestBlockStatsErrorRate:
    """Tests for the BlockStatsWithSamples.error_rate property."""

    def test_block_stats_error_rate_zero_executions(self):
        """error_rate should return 0.0 when total_executions is zero."""
        stats = BlockStatsWithSamples(
            block_id="block-1",
            block_name="TestBlock",
            total_executions=0,
            failed_executions=0,
        )
        assert stats.error_rate == 0.0

    def test_block_stats_error_rate_calculation(self):
        """error_rate should compute (failed/total)*100 correctly."""
        stats = BlockStatsWithSamples(
            block_id="block-1",
            block_name="TestBlock",
            total_executions=10,
            failed_executions=5,
        )
        assert stats.error_rate == 50.0

    def test_block_stats_error_rate_all_failed(self):
        """error_rate should be 100.0 when all executions failed."""
        stats = BlockStatsWithSamples(
            block_id="block-1",
            block_name="TestBlock",
            total_executions=20,
            failed_executions=20,
        )
        assert stats.error_rate == 100.0

    def test_block_stats_error_rate_none_failed(self):
        """error_rate should be 0.0 when no executions failed."""
        stats = BlockStatsWithSamples(
            block_id="block-1",
            block_name="TestBlock",
            total_executions=100,
            failed_executions=0,
        )
        assert stats.error_rate == 0.0


# ---------------------------------------------------------------------------
# Helper: create a BlockErrorMonitor with mocked dependencies
# ---------------------------------------------------------------------------


@pytest.fixture()
def monitor():
    """Create a BlockErrorMonitor with mocked external dependencies."""
    with (
        patch(
            "backend.monitoring.block_error_monitor.get_notification_manager_client"
        ) as mock_notif,
        patch("backend.monitoring.block_error_monitor.Config") as mock_config_cls,
    ):
        mock_cfg = MagicMock()
        mock_cfg.block_error_rate_threshold = 0.5
        mock_cfg.block_error_include_top_blocks = 3
        mock_config_cls.return_value = mock_cfg

        mock_notif.return_value = MagicMock()

        mon = BlockErrorMonitor.__new__(BlockErrorMonitor)
        mon.config = mock_cfg
        mon.notification_client = mock_notif.return_value
        mon.include_top_blocks = 3
        yield mon


# ---------------------------------------------------------------------------
# _mask_sensitive_data tests
# ---------------------------------------------------------------------------


class TestMaskSensitiveData:
    """Tests for BlockErrorMonitor._mask_sensitive_data."""

    @pytest.fixture(autouse=True)
    def _setup(self, monitor):
        self.monitor = monitor

    def test_mask_sensitive_data_numbers(self):
        """Digit sequences should be replaced with X."""
        result = self.monitor._mask_sensitive_data("Error code 12345")
        assert "12345" not in result
        # Numbers should be masked to X
        assert "X" in result

    def test_mask_sensitive_data_uuids(self):
        """UUIDs should be replaced with UUID."""
        msg = "Failed for id 550e8400-e29b-41d4-a716-446655440000"
        result = self.monitor._mask_sensitive_data(msg)
        # After number masking the UUID won't survive intact, but UUID pattern
        # replacement still covers uuid-like patterns.  The key contract: the
        # original UUID must not appear in the output.
        assert "550e8400-e29b-41d4-a716-446655440000" not in result

    def test_mask_sensitive_data_urls(self):
        """URLs should be replaced with URL."""
        result = self.monitor._mask_sensitive_data(
            "Request to https://example.com/api failed"
        )
        assert "https://example.com/api" not in result

    def test_mask_sensitive_data_emails(self):
        """Email addresses should be replaced with EMAIL."""
        result = self.monitor._mask_sensitive_data("Sent to user@example.com")
        assert "user@example.com" not in result

    def test_mask_sensitive_data_paths(self):
        """File paths should be masked."""
        result = self.monitor._mask_sensitive_data(
            "File not found: /home/user/data/file.txt"
        )
        assert "/home/user/data/file.txt" not in result

    def test_mask_sensitive_data_truncation(self):
        """Strings longer than 100 characters should be truncated."""
        long_msg = "A" * 200
        result = self.monitor._mask_sensitive_data(long_msg)
        assert len(result) <= 100

    def test_mask_sensitive_data_none(self):
        """None input should return empty string."""
        result = self.monitor._mask_sensitive_data(None)
        assert result == ""

    def test_mask_sensitive_data_empty_string(self):
        """Empty string input should return empty string."""
        result = self.monitor._mask_sensitive_data("")
        assert result == ""


# ---------------------------------------------------------------------------
# _group_similar_errors tests
# ---------------------------------------------------------------------------


class TestGroupSimilarErrors:
    """Tests for BlockErrorMonitor._group_similar_errors."""

    @pytest.fixture(autouse=True)
    def _setup(self, monitor):
        self.monitor = monitor

    def test_group_similar_errors_empty(self):
        """Empty input should return empty dict."""
        result = self.monitor._group_similar_errors([])
        assert result == {}

    def test_group_similar_errors_none(self):
        """None input should return empty dict."""
        result = self.monitor._group_similar_errors(None)
        assert result == {}

    def test_group_similar_errors_grouping(self):
        """Identical errors should be grouped and sorted by frequency."""
        samples = [
            "Connection timeout",
            "Connection timeout",
            "Connection timeout",
            "Invalid input",
            "Invalid input",
            "Unknown error",
        ]
        result = self.monitor._group_similar_errors(samples)

        assert isinstance(result, dict)
        assert result["Connection timeout"] == 3
        assert result["Invalid input"] == 2
        assert result["Unknown error"] == 1

        # Verify sorted by frequency (most common first)
        keys = list(result.keys())
        assert keys[0] == "Connection timeout"
        assert keys[1] == "Invalid input"
        assert keys[2] == "Unknown error"

    def test_group_similar_errors_single_error(self):
        """Single error sample should return a dict with count 1."""
        result = self.monitor._group_similar_errors(["Some error"])
        assert result == {"Some error": 1}


# ---------------------------------------------------------------------------
# _generate_critical_alerts tests
# ---------------------------------------------------------------------------


class TestGenerateCriticalAlerts:
    """Tests for BlockErrorMonitor._generate_critical_alerts."""

    @pytest.fixture(autouse=True)
    def _setup(self, monitor):
        self.monitor = monitor

    def test_generate_critical_alerts_above_threshold(self):
        """Should generate alert for blocks above the threshold."""
        block_stats = {
            "FailingBlock": BlockStatsWithSamples(
                block_id="block-1",
                block_name="FailingBlock",
                total_executions=100,
                failed_executions=80,
                error_samples=["Connection timeout", "Connection timeout"],
            )
        }
        # threshold=0.5 means 50% -> block has 80% error rate
        alerts = self.monitor._generate_critical_alerts(block_stats, threshold=0.5)
        assert len(alerts) == 1
        assert "FailingBlock" in alerts[0]
        assert "80.0%" in alerts[0]

    def test_generate_critical_alerts_below_threshold(self):
        """Should return empty list for blocks below the threshold."""
        block_stats = {
            "GoodBlock": BlockStatsWithSamples(
                block_id="block-2",
                block_name="GoodBlock",
                total_executions=100,
                failed_executions=1,
                error_samples=[],
            )
        }
        alerts = self.monitor._generate_critical_alerts(block_stats, threshold=0.5)
        assert alerts == []

    def test_generate_critical_alerts_low_volume(self):
        """Should return empty list for blocks with fewer than 10 executions."""
        block_stats = {
            "LowVolumeBlock": BlockStatsWithSamples(
                block_id="block-3",
                block_name="LowVolumeBlock",
                total_executions=5,
                failed_executions=5,
                error_samples=["Error"],
            )
        }
        # Even though error rate is 100%, total_executions < 10
        alerts = self.monitor._generate_critical_alerts(block_stats, threshold=0.5)
        assert alerts == []

    def test_generate_critical_alerts_multiple_blocks(self):
        """Should generate alerts for multiple blocks above threshold."""
        block_stats = {
            "Block_A": BlockStatsWithSamples(
                block_id="a",
                block_name="Block_A",
                total_executions=50,
                failed_executions=40,
                error_samples=["Error A"],
            ),
            "Block_B": BlockStatsWithSamples(
                block_id="b",
                block_name="Block_B",
                total_executions=100,
                failed_executions=90,
                error_samples=["Error B"],
            ),
        }
        alerts = self.monitor._generate_critical_alerts(block_stats, threshold=0.5)
        assert len(alerts) == 2


# ---------------------------------------------------------------------------
# _generate_top_blocks_alert tests
# ---------------------------------------------------------------------------


class TestGenerateTopBlocksAlert:
    """Tests for BlockErrorMonitor._generate_top_blocks_alert."""

    @pytest.fixture(autouse=True)
    def _setup(self, monitor):
        self.monitor = monitor

    def test_generate_top_blocks_alert_no_errors(self):
        """Should return success message when no blocks have errors."""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

        block_stats = {
            "HealthyBlock": BlockStatsWithSamples(
                block_id="block-1",
                block_name="HealthyBlock",
                total_executions=100,
                failed_executions=0,
                error_samples=[],
            )
        }

        result = self.monitor._generate_top_blocks_alert(
            block_stats, start_time, end_time
        )
        assert result is not None
        assert "No errors reported" in result or "running smoothly" in result

    def test_generate_top_blocks_alert_with_errors(self):
        """Should return formatted summary with top error blocks."""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

        block_stats = {
            "ErrorBlock": BlockStatsWithSamples(
                block_id="block-1",
                block_name="ErrorBlock",
                total_executions=50,
                failed_executions=10,
                error_samples=["Connection timeout", "Connection timeout"],
            )
        }

        # Mock _get_error_samples_for_block so it doesn't hit DB
        self.monitor._get_error_samples_for_block = MagicMock(return_value=[])

        result = self.monitor._generate_top_blocks_alert(
            block_stats, start_time, end_time
        )
        assert result is not None
        assert "ErrorBlock" in result
        assert "10 errors" in result

    def test_generate_top_blocks_alert_excludes_low_volume(self):
        """Blocks with fewer than 10 total executions should be excluded."""
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

        block_stats = {
            "LowVolBlock": BlockStatsWithSamples(
                block_id="block-1",
                block_name="LowVolBlock",
                total_executions=5,
                failed_executions=3,
                error_samples=[],
            )
        }

        result = self.monitor._generate_top_blocks_alert(
            block_stats, start_time, end_time
        )
        # Since there are no qualifying blocks, should get "no errors" message
        assert result is not None
        assert "No errors reported" in result or "running smoothly" in result
