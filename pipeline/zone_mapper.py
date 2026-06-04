# pipeline/zone_mapper.py
"""
Maps camera IDs (exactly matching dataset filenames) to store zones.
Store 1: CAM 1, CAM 2, CAM 3, CAM 4, CAM 5
Store 2: entry 1, entry 2, billing_area, zone
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Zone definitions
# Each zone: (x1, y1, x2, y2) in normalized [0,1] coordinates
# so they work regardless of resolution.
# ---------------------------------------------------------------------------

STORE1_ZONES = {
    "CAM 1": [
        {
            "zone_id":   "S1_CAM1_FLOOR",
            "zone_name": "Main Floor - CAM 1",
            "zone_type": "FLOOR",
            "is_revenue_zone": False,
            "bbox": (0.0, 0.0, 1.0, 1.0),
        }
    ],
    "CAM 2": [
        {
            "zone_id":   "S1_CAM2_LEFT_SHELF",
            "zone_name": "Left Shelf",
            "zone_type": "SHELF",
            "is_revenue_zone": True,
            "bbox": (0.0, 0.0, 0.5, 1.0),
        },
        {
            "zone_id":   "S1_CAM2_RIGHT_SHELF",
            "zone_name": "Right Shelf",
            "zone_type": "SHELF",
            "is_revenue_zone": True,
            "bbox": (0.5, 0.0, 1.0, 1.0),
        },
    ],
    "CAM 3": [
        {
            "zone_id":   "S1_CAM3_ENTRY_GATE",
            "zone_name": "Entry/Exit Gate",
            "zone_type": "ENTRY_EXIT",
            "is_revenue_zone": False,
            "bbox": (0.2, 0.0, 0.8, 1.0),
        }
    ],
    "CAM 4": [
        {
            "zone_id":   "S1_CAM4_STORAGE",
            "zone_name": "Storage Area",
            "zone_type": "STORAGE",
            "is_revenue_zone": False,
            "bbox": (0.0, 0.0, 1.0, 1.0),
        }
    ],
    "CAM 5": [
        {
            "zone_id":   "S1_CAM5_BILLING",
            "zone_name": "Billing Counter",
            "zone_type": "BILLING",
            "is_revenue_zone": True,
            "bbox": (0.0, 0.0, 1.0, 1.0),
        }
    ],
}

STORE2_ZONES = {
    "entry 1": [
        {
            "zone_id":   "S2_ENTRY1_GATE",
            "zone_name": "Entry Gate 1",
            "zone_type": "ENTRY_EXIT",
            "is_revenue_zone": False,
            "bbox": (0.1, 0.0, 0.9, 1.0),
        }
    ],
    "entry 2": [
        {
            "zone_id":   "S2_ENTRY2_GATE",
            "zone_name": "Entry Gate 2",
            "zone_type": "ENTRY_EXIT",
            "is_revenue_zone": False,
            "bbox": (0.1, 0.0, 0.9, 1.0),
        }
    ],
    "billing_area": [
        {
            "zone_id":   "S2_BILLING",
            "zone_name": "Billing Area",
            "zone_type": "BILLING",
            "is_revenue_zone": True,
            "bbox": (0.0, 0.0, 1.0, 1.0),
        }
    ],
    "zone": [
        {
            "zone_id":   "S2_ZONE_FLOOR_A",
            "zone_name": "Main Floor Zone A",
            "zone_type": "FLOOR",
            "is_revenue_zone": False,
            "bbox": (0.0, 0.0, 0.5, 1.0),
        },
        {
            "zone_id":   "S2_ZONE_FLOOR_B",
            "zone_name": "Main Floor Zone B",
            "zone_type": "FLOOR",
            "is_revenue_zone": False,
            "bbox": (0.5, 0.0, 1.0, 1.0),
        },
    ],
}

# Map store_id → zone config
ZONE_CONFIG: dict[str, dict] = {
    "store1": STORE1_ZONES,
    "store2": STORE2_ZONES,
}

# ---------------------------------------------------------------------------
# Camera role helpers (used by process_video.py for logic branching)
# ---------------------------------------------------------------------------

ENTRY_EXIT_CAMERAS = {
    "store1": {"CAM 3"},
    "store2": {"entry 1", "entry 2"},
}

BILLING_CAMERAS = {
    "store1": {"CAM 5"},
    "store2": {"billing_area"},
}

STORAGE_CAMERAS = {
    "store1": {"CAM 4"},
    "store2": set(),
}


def get_zones_for_camera(store_id: str, camera_id: str) -> list[dict]:
    """Return zone definitions for a given store + camera."""
    return ZONE_CONFIG.get(store_id, {}).get(camera_id, [])


def is_entry_exit_camera(store_id: str, camera_id: str) -> bool:
    return camera_id in ENTRY_EXIT_CAMERAS.get(store_id, set())


def is_billing_camera(store_id: str, camera_id: str) -> bool:
    return camera_id in BILLING_CAMERAS.get(store_id, set())


def is_storage_camera(store_id: str, camera_id: str) -> bool:
    return camera_id in STORAGE_CAMERAS.get(store_id, set())


def point_in_zone(x_norm: float, y_norm: float, zone: dict) -> bool:
    """Check if a normalized point falls inside a zone bbox."""
    x1, y1, x2, y2 = zone["bbox"]
    return x1 <= x_norm <= x2 and y1 <= y_norm <= y2


def classify_entry_exit(
    y_norm: float,
    prev_y_norm: Optional[float],
    frame_height: int,
) -> Optional[str]:
    """
    Simple top/bottom boundary heuristic for entry/exit cameras.
    Returns 'ENTRY', 'EXIT', or None.
    Top 15% of frame = came from outside (entry).
    Bottom 15% of frame = leaving (exit).
    """
    if prev_y_norm is None:
        return None
    entering = prev_y_norm < 0.15 and y_norm >= 0.15
    exiting  = prev_y_norm > 0.85 and y_norm <= 0.85
    if entering:
        return "ENTRY"
    if exiting:
        return "EXIT"
    return None