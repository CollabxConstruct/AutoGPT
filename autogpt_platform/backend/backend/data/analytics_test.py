"""Tests for backend.data.analytics functions with mocked Prisma."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_prisma():
    """Set up mock Prisma models for AnalyticsDetails and AnalyticsMetrics."""
    with patch("backend.data.analytics.prisma") as mock_prisma_module:
        # Mock AnalyticsDetails.prisma().create(...)
        details_actions = MagicMock()
        details_actions.create = AsyncMock(return_value=MagicMock(id="detail-1"))
        details_model = MagicMock()
        details_model.prisma.return_value = details_actions
        mock_prisma_module.models.AnalyticsDetails = details_model

        # Mock AnalyticsMetrics.prisma().create(...)
        metrics_actions = MagicMock()
        metrics_actions.create = AsyncMock(return_value=MagicMock(id="metric-1"))
        metrics_model = MagicMock()
        metrics_model.prisma.return_value = metrics_actions
        mock_prisma_module.models.AnalyticsMetrics = metrics_model

        # Mock prisma.types so the CreateInput classes resolve
        mock_prisma_module.types.AnalyticsDetailsCreateInput = dict
        mock_prisma_module.types.AnalyticsMetricsCreateInput = dict

        yield {
            "module": mock_prisma_module,
            "details_create": details_actions.create,
            "metrics_create": metrics_actions.create,
        }


@pytest.mark.asyncio
async def test_log_raw_analytics(mock_prisma):
    """log_raw_analytics calls prisma create with the correct data."""
    from backend.data.analytics import log_raw_analytics

    result = await log_raw_analytics(
        user_id="user-123",
        type="page_view",
        data={"page": "/home", "referrer": "google.com"},
        data_index="page_view_idx",
    )

    mock_prisma["details_create"].assert_called_once()
    call_kwargs = mock_prisma["details_create"].call_args
    create_data = call_kwargs.kwargs["data"]
    assert create_data["userId"] == "user-123"
    assert create_data["type"] == "page_view"
    assert create_data["dataIndex"] == "page_view_idx"
    assert result.id == "detail-1"


@pytest.mark.asyncio
async def test_log_raw_metric_valid(mock_prisma):
    """log_raw_metric calls prisma create with the correct data for valid input."""
    from backend.data.analytics import log_raw_metric

    result = await log_raw_metric(
        user_id="user-456",
        metric_name="execution_time",
        metric_value=3.14,
        data_string="some context",
    )

    mock_prisma["metrics_create"].assert_called_once()
    call_kwargs = mock_prisma["metrics_create"].call_args
    create_data = call_kwargs.kwargs["data"]
    assert create_data["userId"] == "user-456"
    assert create_data["analyticMetric"] == "execution_time"
    assert create_data["value"] == 3.14
    assert create_data["dataString"] == "some context"
    assert result.id == "metric-1"


@pytest.mark.asyncio
async def test_log_raw_metric_negative_value(mock_prisma):
    """log_raw_metric raises ValueError for negative metric_value."""
    from backend.data.analytics import log_raw_metric

    with pytest.raises(ValueError, match="metric_value must be non-negative"):
        await log_raw_metric(
            user_id="user-789",
            metric_name="latency",
            metric_value=-1.0,
            data_string="negative test",
        )

    # Prisma create should never have been called
    mock_prisma["metrics_create"].assert_not_called()
