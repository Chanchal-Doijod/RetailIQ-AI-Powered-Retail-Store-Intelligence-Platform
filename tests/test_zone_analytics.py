# PROMPT:
# Generate unit tests for get_zone_analytics inside zone_analytics.py.
# Cover target frequency tracking loops and handle unexpected Exception triggers.

# CHANGES MADE:
# Injected mock file exception logic blocks to evaluate error handling routing paths.

import pytest
from unittest.mock import patch, mock_open
from app.zone_analytics import get_zone_analytics

MOCK_ANALYTICS_LOGS = (
    '{"zone_id": "MAKEUP"}\n'
    '{"zone_id": "SKINCARE"}\n'
    '{"zone_id": "MAKEUP"}\n'
)

def test_zone_analytics_aggregation_success():
    """Verify dictionary tracker keys match event appearance totals perfectly."""
    with patch("builtins.open", mock_open(read_data=MOCK_ANALYTICS_LOGS)):
        counts = get_zone_analytics()
        assert counts["MAKEUP"] == 2
        assert counts["SKINCARE"] == 1

def test_zone_analytics_file_exception():
    """Ensure runtime system exceptions return a structured error description key."""
    with patch("builtins.open", side_effect=IOError("Permission Denied")):
        result = get_zone_analytics()
        assert "error" in result
        assert "Permission Denied" in result["error"]