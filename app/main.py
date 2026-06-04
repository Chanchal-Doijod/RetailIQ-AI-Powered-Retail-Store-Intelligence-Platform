# app/main.py
"""
FastAPI application.
Endpoints:
  POST /events/ingest
  GET  /stores/{store_id}/metrics
  GET  /stores/{store_id}/funnel
  GET  /stores/{store_id}/heatmap
  GET  /stores/{store_id}/anomalies
  GET  /health
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.metrics import calculate_metrics
from app.funnel import calculate_funnel
from app.heatmap import calculate_heatmap
from app.dashboard import get_dashboard

EVENTS_PATH = os.environ.get("EVENTS_OUTPUT", "data/output/events.jsonl")

# Camera feed staleness threshold (seconds)
STALE_FEED_THRESHOLD = int(os.environ.get("STALE_FEED_THRESHOLD", "120"))

# In-memory camera heartbeat registry
# camera_id → last seen timestamp
_camera_last_seen: dict[str, float] = {}
# store_id → set of known cameras
_store_cameras: dict[str, set] = defaultdict(set)

app = FastAPI(
    title="Retail Store Intelligence API",
    version="1.0.0",
    description="Video analytics pipeline for Apex Retail",
)

@app.get("/dashboard")
def dashboard():
    try:
        return get_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class EventPayload(BaseModel):
    event_type:      str
    id_token:        Optional[str]  = None
    track_id:        Optional[int]  = None
    store_id:        Optional[str]  = None
    store_code:      Optional[str]  = None
    camera_id:       Optional[str]  = None
    zone_id:         Optional[str]  = None
    zone_name:       Optional[str]  = None
    zone_type:       Optional[str]  = None
    event_timestamp: Optional[str]  = None
    event_time:      Optional[str]  = None
    is_staff:        bool           = False
    gender_pred:     Optional[str]  = None
    age_pred:        Optional[int]  = None
    age_bucket:      Optional[str]  = None
    dwell_seconds:   Optional[float] = None
    queue_wait_seconds: Optional[float] = None
    queue_length:    Optional[int]  = None
    reentry_count:   Optional[int]  = None
    is_revenue_zone: Optional[bool] = None
    zone_hotspot_x:  Optional[float] = None
    zone_hotspot_y:  Optional[float] = None
    group_id:        Optional[str]  = None
    group_size:      Optional[int]  = None
    is_face_hidden:  bool           = False

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

_anomaly_store: dict[str, list[dict]] = defaultdict(list)

# Rolling window for queue spike detection
_queue_join_times: dict[str, list[float]] = defaultdict(list)
QUEUE_SPIKE_WINDOW   = 300.0   # 5 min
QUEUE_SPIKE_THRESH   = 5       # N joins in window = spike
CONVERSION_DROP_THRESH = 0.15  # If conversion drops by this much, alert
_prev_conversion: dict[str, float] = {}


def _check_anomalies(store_id: str, event: dict):
    now = time.time()
    etype = event.get("event_type", "")

    # 1. Billing queue spike
    if etype == "billing_queue_join":
        cam = event.get("camera_id", "")
        key = f"{store_id}:{cam}"
        times = _queue_join_times[key]
        times.append(now)
        # Prune old
        _queue_join_times[key] = [t for t in times if now - t <= QUEUE_SPIKE_WINDOW]
        if len(_queue_join_times[key]) >= QUEUE_SPIKE_THRESH:
            _anomaly_store[store_id].append({
                "type":       "QUEUE_SPIKE",
                "camera_id":  cam,
                "count":      len(_queue_join_times[key]),
                "window_sec": QUEUE_SPIKE_WINDOW,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "severity":   "HIGH",
            })

    # 2. Update camera heartbeat
    cam_id = event.get("camera_id")
    if cam_id:
        _camera_last_seen[f"{store_id}:{cam_id}"] = now
        _store_cameras[store_id].add(cam_id)


def _get_stale_feeds(store_id: str) -> list[dict]:
    now = time.time()
    stale = []
    for cam_id in _store_cameras.get(store_id, set()):
        key = f"{store_id}:{cam_id}"
        last = _camera_last_seen.get(key)
        if last is None or (now - last) > STALE_FEED_THRESHOLD:
            stale.append({
                "camera_id":   cam_id,
                "last_seen":   datetime.fromtimestamp(last, tz=timezone.utc).isoformat()
                               if last else None,
                "seconds_ago": round(now - last, 1) if last else None,
                "status":      "STALE",
            })
    return stale


def _detect_conversion_drop(store_id: str) -> Optional[dict]:
    try:
        m = calculate_metrics(store_id, window_minutes=30)
        curr = m["conversion_rate"]
        prev = _prev_conversion.get(store_id)
        _prev_conversion[store_id] = curr
        if prev is not None and (prev - curr) >= CONVERSION_DROP_THRESH:
            return {
                "type":        "CONVERSION_DROP",
                "previous":    prev,
                "current":     curr,
                "drop":        round(prev - curr, 4),
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "severity":    "MEDIUM",
            }
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status":    "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version":   "1.0.0",
    }


@app.post("/events/ingest")
def ingest_event(payload: EventPayload):
    """
    Accepts a single event from the video pipeline.
    Persists to events.jsonl and updates in-memory anomaly state.
    """
    event = payload.dict(exclude_none=False)
    # Normalize store_id
    store_id = event.get("store_id") or event.get("store_code") or "unknown"
    event["store_id"] = store_id

    # Timestamp fallback
    if not event.get("event_timestamp"):
        event["event_timestamp"] = datetime.now(timezone.utc).isoformat()

    # Persist
    path = Path(EVENTS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")

    # Anomaly checks
    _check_anomalies(store_id, event)

    return {"status": "accepted", "event_type": event["event_type"]}

@app.get("/diagnostics")
def diagnostics():

    metrics = calculate_metrics("store2")

    return {
        "customer_count": metrics["total_visitors"],
        "staff_count": metrics["total_staff"],
        "events_generated": metrics["total_events"],
    }

@app.post("/events/ingest/batch")
def ingest_batch(events: list[EventPayload]):
    results = []
    for ev in events:
        r = ingest_event(ev)
        results.append(r)
    return {"accepted": len(results), "results": results}


@app.get("/stores/{store_id}/metrics")
def get_metrics(
    store_id: str,
    window_minutes: int = Query(60, ge=1, le=1440),
):
    try:
        return calculate_metrics(store_id, window_minutes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stores/{store_id}/funnel")
def get_funnel(store_id: str):
    try:
        return calculate_funnel(store_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stores/{store_id}/heatmap")
def get_heatmap(
    store_id: str,
    camera_id: Optional[str] = Query(None),
):
    try:
        return calculate_heatmap(store_id, camera_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stores/{store_id}/anomalies")
def get_anomalies(store_id: str):
    anomalies = list(_anomaly_store.get(store_id, []))

    # Add stale feed anomalies
    stale = _get_stale_feeds(store_id)
    for s in stale:
        anomalies.append({
            "type":       "STALE_FEED",
            "camera_id":  s["camera_id"],
            "last_seen":  s["last_seen"],
            "seconds_ago": s["seconds_ago"],
            "severity":   "HIGH",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        })

    # Conversion drop check
    conv_drop = _detect_conversion_drop(store_id)
    if conv_drop:
        anomalies.append(conv_drop)

    # Sort by severity
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 2))

    return {
        "store_id":       store_id,
        "anomaly_count":  len(anomalies),
        "anomalies":      anomalies,
        "as_of":          datetime.now(timezone.utc).isoformat(),
    }
