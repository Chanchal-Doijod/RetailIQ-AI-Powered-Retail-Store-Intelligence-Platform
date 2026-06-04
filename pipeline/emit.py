# pipeline/emit.py
"""
Emit standardized JSON event messages to output/events.jsonl.
Schema matches sample_events.jsonl exactly.
All pipeline code calls these functions — never hand-rolls JSON.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional

# FIXED: Explicit absolute fallback routing ensuring data writes even if environment variables reset
OUTPUT_PATH = "F:/store-intelligence/data/output/events.jsonl"
_lock = threading.Lock()


def _ts(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def _write(event: dict) -> dict:
    # Ensure directory path structures are cleanly generated
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with _lock:
        # Open in append mode ('a') to smoothly capture sequential video metrics
        with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
            f.flush()                  # Force Python to pass data immediately to OS
            try:
                os.fsync(f.fileno())   # Force Windows to instantly commit stream line to storage disk
            except OSError:
                pass                   # Protects execution if running in virtualized system environments
    return event


# ---------------------------------------------------------------------------
# ENTRY
# ---------------------------------------------------------------------------

def emit_entry(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    is_staff: bool = False,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    age_bucket: Optional[str] = None,
    is_face_hidden: bool = False,
    group_id: Optional[str] = None,
    group_size: Optional[int] = None,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":      "entry",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "event_timestamp": _ts(timestamp),
        "is_staff":        is_staff,
        "gender_pred":     gender,
        "age_pred":        age,
        "age_bucket":      age_bucket,
        "is_face_hidden":  is_face_hidden,
        "group_id":        group_id,
        "group_size":      group_size,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# EXIT
# ---------------------------------------------------------------------------

def emit_exit(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    is_staff: bool = False,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    age_bucket: Optional[str] = None,
    dwell_seconds: Optional[float] = None,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":      "exit",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "event_timestamp": _ts(timestamp),
        "is_staff":        is_staff,
        "gender_pred":     gender,
        "age_pred":        age,
        "age_bucket":      age_bucket,
        "dwell_seconds":   dwell_seconds,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# REENTRY
# ---------------------------------------------------------------------------

def emit_reentry(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    reentry_count: int = 2,
    is_staff: bool = False,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":      "reentry",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "event_timestamp": _ts(timestamp),
        "is_staff":        is_staff,
        "reentry_count":   reentry_count,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# ZONE_ENTER
# ---------------------------------------------------------------------------

def emit_zone_enter(
    *,
    visitor_id: str,
    track_id: int,
    store_id: str,
    camera_id: str,
    zone_id: str,
    zone_name: str,
    zone_type: str,
    is_revenue_zone: bool = False,
    timestamp: Optional[datetime] = None,
    hotspot_x: Optional[float] = None,
    hotspot_y: Optional[float] = None,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    age_bucket: Optional[str] = None,
) -> dict:
    event = {
        "event_type":      "zone_entered",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "zone_id":         zone_id,
        "zone_name":       zone_name,
        "zone_type":       zone_type,
        "is_revenue_zone": is_revenue_zone,
        "event_timestamp": _ts(timestamp),
        "zone_hotspot_x":  hotspot_x,
        "zone_hotspot_y":  hotspot_y,
        "gender_pred":     gender,
        "age_pred":        age,
        "age_bucket":      age_bucket,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# ZONE_EXIT
# ---------------------------------------------------------------------------

def emit_zone_exit(
    *,
    visitor_id: str,
    track_id: int,
    store_id: str,
    camera_id: str,
    zone_id: str,
    zone_name: str,
    zone_type: str,
    is_revenue_zone: bool = False,
    timestamp: Optional[datetime] = None,
    dwell_seconds: Optional[float] = None,
    hotspot_x: Optional[float] = None,
    hotspot_y: Optional[float] = None,
    gender: Optional[str] = None,
    age: Optional[int] = None,
) -> dict:
    event = {
        "event_type":      "zone_exited",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "zone_id":         zone_id,
        "zone_name":       zone_name,
        "zone_type":       zone_type,
        "is_revenue_zone": is_revenue_zone,
        "event_timestamp": _ts(timestamp),
        "dwell_seconds":   dwell_seconds,
        "zone_hotspot_x":  hotspot_x,
        "zone_hotspot_y":  hotspot_y,
        "gender_pred":     gender,
        "age_pred":        age,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# ZONE_DWELL
# ---------------------------------------------------------------------------

def emit_zone_dwell(
    *,
    visitor_id: str,
    track_id: int,
    store_id: str,
    camera_id: str,
    zone_id: str,
    zone_name: str,
    dwell_seconds: float,
    timestamp: Optional[datetime] = None,
    hotspot_x: Optional[float] = None,
    hotspot_y: Optional[float] = None,
) -> dict:
    event = {
        "event_type":      "zone_dwell",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "zone_id":         zone_id,
        "zone_name":       zone_name,
        "event_timestamp": _ts(timestamp),
        "dwell_seconds":   dwell_seconds,
        "zone_hotspot_x":  hotspot_x,
        "zone_hotspot_y":  hotspot_y,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# BILLING_QUEUE_JOIN
# ---------------------------------------------------------------------------

def emit_queue_join(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    queue_length: Optional[int] = None,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":      "billing_queue_join",
        "id_token":        visitor_id,
        "track_id":        track_id,
        "store_id":        store_id,
        "camera_id":       camera_id,
        "event_timestamp": _ts(timestamp),
        "queue_length":    queue_length,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# BILLING_QUEUE_ABANDON
# ---------------------------------------------------------------------------

def emit_queue_abandon(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    wait_seconds: Optional[float] = None,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":        "billing_queue_abandon",
        "id_token":          visitor_id,
        "track_id":          track_id,
        "store_id":          store_id,
        "camera_id":         camera_id,
        "event_timestamp":   _ts(timestamp),
        "queue_wait_seconds": wait_seconds,
    }
    return _write(event)


# ---------------------------------------------------------------------------
# QUEUE_COMPLETED
# ---------------------------------------------------------------------------

def emit_queue_completed(
    *,
    visitor_id: str,
    store_id: str,
    camera_id: str,
    timestamp: Optional[datetime] = None,
    wait_seconds: Optional[float] = None,
    track_id: Optional[int] = None,
) -> dict:
    event = {
        "event_type":        "queue_completed",
        "id_token":          visitor_id,
        "track_id":          track_id,
        "store_id":          store_id,
        "camera_id":         camera_id,
        "event_timestamp":   _ts(timestamp),
        "queue_wait_seconds": wait_seconds,
    }
    return _write(event)


if __name__ == "__main__":
    # Local terminal testing routing confirmation
    test_event = emit_entry(
        visitor_id="test_visitor_001",
        store_id="store1",
        camera_id="CAM 1",
        track_id=42
    )
    print("Success: Native Event Saved Cleanly:")
    print(json.dumps(test_event, indent=2))