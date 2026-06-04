# PROMPT:
# Generate pytest scripts evaluating the calculate_funnel logic in app/funnel.py.
# Ensure progression logic counts drop-off rates correctly between consecutive stages.

# CHANGES MADE:
# Hardcoded distinct behavioral customer keys to map stage progression lengths cleanly.

import pytest
from unittest.mock import patch, mock_open
from app.funnel import calculate_funnel

MOCK_FUNNEL_LOGS = (
    '{"event_type": "entry", "id_token": "CUST_01", "store_id": "store1", "is_staff": false}\n'
    '{"event_type": "zone_entered", "id_token": "CUST_01", "store_id": "store1", "zone_id": "SKINCARE"}\n'
    '{"event_type": "billing_queue_join", "id_token": "CUST_01", "store_id": "store1"}\n'
    '{"event_type": "queue_completed", "id_token": "CUST_01", "store_id": "store1"}\n'
    '{"event_type": "entry", "id_token": "CUST_02", "store_id": "store1", "is_staff": false}\n'
)

@patch("app.metrics.Path.exists", return_value=True)
def test_funnel_progression_metrics(mock_exists):
    """Verify customer counts drop off accurately across sequential stages."""
    with patch("builtins.open", mock_open(read_data=MOCK_FUNNEL_LOGS)):
        funnel = calculate_funnel(store_id="store1")
        
        # Checking funnel lengths
        assert funnel["stages"]["entered_store"] == 2
        assert funnel["stages"]["browsed_zone"] == 1
        assert funnel["stages"]["reached_billing"] == 1
        assert funnel["stages"]["converted"] == 1
        
        # Checking step rate drop-offs
        assert funnel["drop_off_rates"]["entered_store_to_browsed_zone"] == 0.50
        assert funnel["drop_off_rates"]["browsed_zone_to_reached_billing"] == 0.0