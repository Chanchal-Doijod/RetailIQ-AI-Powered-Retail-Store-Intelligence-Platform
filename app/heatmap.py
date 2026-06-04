# app/heatmap.py
"""
Spatial heatmap generation.
Aggregates zone_dwell, zone_entered, zone_exited events into a
dwell-weighted grid. Each cell value = total dwell seconds in that region.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional
import os

EVENTS_PATH = os.environ.get("EVENTS_OUTPUT", "data/output/events.jsonl")

# Grid resolution
GRID_W = 20
GRID_H = 20


def _load_zone_events(store_id: str) -> list[dict]:
    events = []
    path = Path(EVENTS_PATH)
    if not path.exists():
        return events
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = ev.get("store_id") or ev.get("store_code", "")
            if store_id not in (sid, sid.replace("store_", "store")):
                continue
            if ev.get("event_type") not in (
                "zone_entered", "zone_exited", "zone_dwell"
            ):
                continue
            events.append(ev)
    return events


def calculate_heatmap(
    store_id: str,
    camera_id: Optional[str] = None,
) -> dict:
    events = _load_zone_events(store_id)
    if camera_id:
        events = [e for e in events if e.get("camera_id") == camera_id]

    # Grid: (row, col) → total dwell seconds
    grid: dict[tuple, float] = defaultdict(float)
    # Zone-level aggregation
    zone_stats: dict[str, dict] = defaultdict(
        lambda: {"total_dwell": 0.0, "visit_count": 0, "avg_dwell": 0.0}
    )

    for ev in events:
        etype = ev.get("event_type")
        hx = ev.get("zone_hotspot_x")
        hy = ev.get("zone_hotspot_y")
        dwell = ev.get("dwell_seconds", 0.0) or 0.0
        zid   = ev.get("zone_id", "UNKNOWN")

        # Zone-level stats
        if etype in ("zone_exited", "zone_dwell") and dwell > 0:
            zone_stats[zid]["total_dwell"] += dwell
            if etype == "zone_exited":
                zone_stats[zid]["visit_count"] += 1

        # Grid cell (from normalized hotspot coordinates)
        if hx is not None and hy is not None:
            col = min(int(hx * GRID_W), GRID_W - 1)
            row = min(int(hy * GRID_H), GRID_H - 1)
            weight = dwell if dwell > 0 else 1.0   # visits count even with 0 dwell
            grid[(row, col)] += weight

    # Compute avg dwell per zone
    for zid, stats in zone_stats.items():
        vc = stats["visit_count"]
        if vc > 0:
            stats["avg_dwell"] = round(stats["total_dwell"] / vc, 1)
        stats["total_dwell"] = round(stats["total_dwell"], 1)

    # Serialize grid as list of {row, col, value}
    max_val = max(grid.values(), default=1.0)
    grid_cells = [
        {
            "row":       r,
            "col":       c,
            "value":     round(v, 1),
            "intensity": round(v / max_val, 4),
        }
        for (r, c), v in grid.items()
    ]
    grid_cells.sort(key=lambda x: x["value"], reverse=True)

    # Top hotspots
    top_hotspots = grid_cells[:10]

    return {
        "store_id":       store_id,
        "camera_id":      camera_id,
        "grid_width":     GRID_W,
        "grid_height":    GRID_H,
        "grid_cells":     grid_cells,
        "top_hotspots":   top_hotspots,
        "zone_stats":     dict(zone_stats),
        "total_events":   len(events),
    }
