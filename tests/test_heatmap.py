# PROMPT:
# Generate unit tests for calculate_heatmap parsing normalized spatial points.
# Verify correct row/col bounding constraints inside the 20x20 cell matrix layout.

# CHANGES MADE:
# Provided precise float hotspot values to test border math conditions securely.

import pytest
from unittest.mock import patch, mock_open
from app.heatmap import calculate_heatmap

MOCK_HEATMAP_LOGS = (
    '{"event_type": "zone_entered", "store_id": "store1", "camera_id": "CAM6", "zone_id": "S2_BILLING", "zone_hotspot_x": 0.5, "zone_hotspot_y": 0.5, "dwell_seconds": 10.0}\n'
    '{"event_type": "zone_dwell", "store_id": "store1", "camera_id": "CAM6", "zone_id": "S2_BILLING", "zone_hotspot_x": 0.999, "zone_hotspot_y": 0.999, "dwell_seconds": 20.0}\n'
)

@patch("app.heatmap.Path.exists", return_value=True)
def test_heatmap_grid_mapping(mock_exists):
    """Confirm raw floating point positions scale correctly into 0-19 grid coordinates."""
    with patch("builtins.open", mock_open(read_data=MOCK_HEATMAP_LOGS)):
        heatmap = calculate_heatmap(store_id="store1", camera_id="CAM6")
        
        assert heatmap["grid_width"] == 20
        assert heatmap["grid_height"] == 20
        assert len(heatmap["grid_cells"]) > 0
        
        # Test boundary overflow mapping constraint (0.999 * 20 should round to cell 19)
        top_cell = heatmap["grid_cells"][0]
        assert top_cell["row"] == 19
        assert top_cell["col"] == 19