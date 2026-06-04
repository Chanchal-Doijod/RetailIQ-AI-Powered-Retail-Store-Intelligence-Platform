# pipeline/process_video.py
"""
Main video processing pipeline.
- YOLOv8 person detection
- ByteTrack multi-object tracking
- Fallback Spatial IOU + HSV-based appearance ReID (cross-frame identity linking)
- Staff detection (multi-signal: zone, motion, dwell, appearance)
- ZONE-GATED ENTRY / EXIT event generation with Dwell Verification Filters
- ZONE_ENTER / ZONE_EXIT / ZONE_DWELL event generation with Debounce Protection
- Billing queue detection (CAM5 / billing_area)
"""

import argparse
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("Install ultralytics: pip install ultralytics")

from pipeline.emit import (
    emit_entry,
    emit_exit,
    emit_queue_abandon,
    emit_queue_completed,
    emit_queue_join,
    emit_reentry,
    emit_zone_dwell,
    emit_zone_enter,
    emit_zone_exit,
)
from pipeline.zone_mapper import (
    get_zones_for_camera,
    is_billing_camera,
    is_entry_exit_camera,
    is_storage_camera,
    point_in_zone,
)

# ---------------------------------------------------------------------------
# Global Shared Baselines
# ---------------------------------------------------------------------------

YOLO_MODEL        = os.environ.get("YOLO_MODEL", "yolov8n.pt")
IOU_THRESHOLD     = float(os.environ.get("YOLO_IOU", "0.30"))  
ZONE_DWELL_TICK   = 10.0          
REENTRY_WINDOW    = 60.0          
QUEUE_MIN_DWELL   = 8.0           
QUEUE_ABANDON_MAX = 120.0         
STAFF_STORAGE_CAM_THRESHOLD = 3   
STAFF_DWELL_THRESHOLD = 600.0     
APPEAR_HIST_BINS  = 32

# Smoothing buffers
TRACK_MAX_LOST_FRAMES = 90        # Frame cache window to hold blinking identities
ZONE_DEBOUNCE_FRAMES  = 20        # Smooths border boundary noise


def _compute_iou(boxA, boxB):
    """Compute Intersection over Union of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    if float(boxAArea + boxBArea - interArea) == 0:
        return 0
    return interArea / float(boxAArea + boxBArea - interArea)


# ---------------------------------------------------------------------------
# HSV Appearance ReID Registry
# ---------------------------------------------------------------------------

class ReIDRegistry:
    def __init__(self, similarity_threshold: float = 0.92):
        self.threshold   = similarity_threshold
        self._pool: dict[str, dict] = {}

    def _compute_hist(self, crop: np.ndarray) -> np.ndarray:
        if crop is None or crop.size == 0:
            return np.zeros(APPEAR_HIST_BINS * 3, dtype=np.float32)
        hsv   = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hists = []
        for ch in range(3):
            h = cv2.calcHist([hsv], [ch], None, [APPEAR_HIST_BINS], [0, 256])
            cv2.normalize(h, h)
            hists.append(h.flatten())
        return np.concatenate(hists)

    def match_or_create(
        self,
        crop: np.ndarray,
        now: float,
        is_staff_hint: bool = False,
    ) -> tuple[str, bool, int]:
        hist = self._compute_hist(crop)
        best_id, best_score = None, -1.0

        for vid, info in self._pool.items():
            score = cv2.compareHist(
                hist.reshape(-1, 1).astype(np.float32),
                info["hist"].reshape(-1, 1).astype(np.float32),
                cv2.HISTCMP_CORREL,
            )
            is_recent_or_active = (
                info.get("exit_time") is None or 
                (now - info["exit_time"]) < REENTRY_WINDOW
            )
            if score > self.threshold and score > best_score and is_recent_or_active:
                best_id, best_score = vid, score

        if best_id:
            info = self._pool[best_id]
            info["hist"]         = hist          
            info["last_seen"]    = now
            is_actual_reentry = info["exit_time"] is not None
            info["exit_time"]    = None          
            
            if is_actual_reentry:
                info["entry_count"] += 1
                return best_id, True, info["entry_count"]
            else:
                return best_id, False, info["entry_count"]
        else:
            vid = f"VIS_{int(now)}_{len(self._pool) + 1}"
            self._pool[vid] = {
                "hist":        hist,
                "last_seen":   now,
                "exit_time":   None,
                "is_staff":    is_staff_hint,
                "entry_count": 1,
            }
            return vid, False, 1

    def mark_exit(self, visitor_id: str, now: float):
        if visitor_id in self._pool:
            self._pool[visitor_id]["exit_time"] = now

    def update_seen(self, visitor_id: str, now: float):
        if visitor_id in self._pool:
            self._pool[visitor_id]["last_seen"] = now

    def set_staff(self, visitor_id: str):
        if visitor_id in self._pool:
            self._pool[visitor_id]["is_staff"] = True

    def is_staff(self, visitor_id: str) -> bool:
        return self._pool.get(visitor_id, {}).get("is_staff", False)


# ---------------------------------------------------------------------------
# Staff Classifier (FIXED HSV COLOR MAPPING)
# ---------------------------------------------------------------------------

class StaffClassifier:
    def __init__(self, store_id: str, camera_id: str):
        self.store_id  = store_id
        self.camera_id = camera_id
        self._storage  = is_storage_camera(store_id, camera_id)
        self._storage_frames: dict[int, int] = defaultdict(int)
        self._first_seen: dict[str, float] = {}
        self._revenue_visits: dict[str, int] = defaultdict(int)
        self._short_cycles: dict[str, int] = defaultdict(int)
        self._last_entry: dict[str, float] = {}

    def record_entry(self, visitor_id: str, now: float):
        if visitor_id not in self._first_seen:
            self._first_seen[visitor_id] = now
        if visitor_id in self._last_entry:
            cycle = now - self._last_entry[visitor_id]
            if cycle < 30:
                self._short_cycles[visitor_id] += 1
        self._last_entry[visitor_id] = now

    def record_revenue_zone(self, visitor_id: str):
        self._revenue_visits[visitor_id] += 1

    def classify(
        self,
        visitor_id: str,
        track_id: int,
        crop: np.ndarray,
        now: float,
        in_storage_zone: bool = False,
    ) -> bool:
        # Failsafe 1: Identify stationary cashiers instantly at billing desk counters
        first = self._first_seen.get(visitor_id)
        if "billing" in self.camera_id or "billing" in getattr(self, "camera_id", ""):
            if first and (now - first) > 90.0:  # If here for 1.5+ minutes stationary, it's staff
                return True

        if self._storage:
            if in_storage_zone:
                self._storage_frames[track_id] += 1
            if self._storage_frames[track_id] >= STAFF_STORAGE_CAM_THRESHOLD:
                return True  

        if first and (now - first) > STAFF_DWELL_THRESHOLD:
            if self._revenue_visits.get(visitor_id, 0) == 0:
                return True

        if self._short_cycles.get(visitor_id, 0) >= 3:
            return True

        # Failsafe 2: Precise Multi-Store Uniform Color Space Classifications
        if crop is not None and crop.size > 0:
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            h_mean = hsv[:, :, 0].mean()  # Hue
            s_mean = hsv[:, :, 1].mean()  # Saturation
            v_mean = hsv[:, :, 2].mean()  # Value/Brightness

            # Profile A: Store 1 Black Uniform Shirts (Low value, low saturation)
            if v_mean < 80 and s_mean < 60:
                return True
                
            # Profile B: Store 2 Hot Pink Top Uniforms (Hue 140-170, High Saturation & Brightness)
            elif 135 <= h_mean <= 172 and s_mean > 85 and v_mean > 85:
                return True  

        return False


# ---------------------------------------------------------------------------
# Zone Tracker
# ---------------------------------------------------------------------------

class ZoneTracker:
    def __init__(self, zones: list[dict], fps: float):
        self.zones = zones
        self.fps   = max(fps, 1.0)
        # track_id → {zone_id: {enter_frame, last_dwell_frame, outside_streak, frame_count_inside}}
        self._active: dict[int, dict[str, dict]] = defaultdict(dict)

    def update(
        self,
        track_id: int,
        visitor_id: str,
        store_id: str,
        camera_id: str,
        x_norm: float,
        y_norm: float,
        frame_idx: int,
        timestamp: datetime,
    ) -> list[dict]:
        events = []
        now_frame = frame_idx
        active = self._active[track_id]

        for zone in self.zones:
            zid   = zone["zone_id"]
            inside = point_in_zone(x_norm, y_norm, zone)

            if inside:
                if zid not in active:
                    active[zid] = {
                        "enter_frame":      now_frame,
                        "last_dwell_frame": now_frame,
                        "outside_streak":   0,
                        "frame_count_inside": 2  
                    }
                    events.append({
                        "fn": emit_zone_enter,
                        "kwargs": dict(
                            visitor_id=visitor_id, track_id=track_id, store_id=store_id, camera_id=camera_id,
                            zone_id=zid, zone_name=zone["zone_name"], zone_type=zone["zone_type"],
                            is_revenue_zone=zone["is_revenue_zone"], timestamp=timestamp,
                            hotspot_x=round(x_norm, 3), hotspot_y=round(y_norm, 3),
                        ),
                    })
                else:
                    active[zid]["outside_streak"] = 0
                    active[zid]["frame_count_inside"] += 2
                    
                    frames_in = now_frame - active[zid]["last_dwell_frame"]
                    if (frames_in / self.fps) >= ZONE_DWELL_TICK:
                        total_secs = (now_frame - active[zid]["enter_frame"]) / self.fps
                        active[zid]["last_dwell_frame"] = now_frame
                        events.append({
                            "fn": emit_zone_dwell,
                            "kwargs": dict(
                                visitor_id=visitor_id, track_id=track_id, store_id=store_id, camera_id=camera_id,
                                zone_id=zid, zone_name=zone["zone_name"], dwell_seconds=round(total_secs, 1),
                                timestamp=timestamp, hotspot_x=round(x_norm, 3), hotspot_y=round(y_norm, 3),
                            ),
                        })
            else:
                if zid in active:
                    active[zid]["outside_streak"] += 2
                    if active[zid]["outside_streak"] >= ZONE_DEBOUNCE_FRAMES:
                        total_secs = (now_frame - active[zid]["enter_frame"]) / self.fps
                        events.append({
                            "fn": emit_zone_exit,
                            "kwargs": dict(
                                visitor_id=visitor_id, track_id=track_id, store_id=store_id, camera_id=camera_id,
                                zone_id=zid, zone_name=zone["zone_name"], zone_type=zone["zone_type"],
                                is_revenue_zone=zone["is_revenue_zone"], timestamp=timestamp,
                                dwell_seconds=round(total_secs, 1), hotspot_x=round(x_norm, 3), hotspot_y=round(y_norm, 3),
                            ),
                        })
                        del active[zid]

        return events

    def is_inside_zone_type_verified(self, track_id: int, zone_type: str, min_dwell_frames: int) -> bool:
        active = self._active.get(track_id, {})
        for zid, info in active.items():
            zone = next((z for z in self.zones if z["zone_id"] == zid), None)
            if zone and zone.get("zone_type") == zone_type:
                if info.get("frame_count_inside", 0) >= min_dwell_frames:
                    return True
        return False

    def flush_all(
        self,
        track_id: int,
        visitor_id: str,
        store_id: str,
        camera_id: str,
        frame_idx: int,
        timestamp: datetime,
    ) -> list[dict]:
        events = []
        active = self._active.get(track_id, {})
        for zid, info in list(active.items()):
            zone = next((z for z in self.zones if z["zone_id"] == zid), None)
            if zone:
                total_secs = (frame_idx - info["enter_frame"]) / self.fps
                events.append({
                    "fn": emit_zone_exit,
                    "kwargs": dict(
                        visitor_id=visitor_id, track_id=track_id, store_id=store_id, camera_id=camera_id,
                        zone_id=zid, zone_name=zone["zone_name"], zone_type=zone["zone_type"],
                        is_revenue_zone=zone["is_revenue_zone"], timestamp=timestamp,
                        dwell_seconds=round(total_secs, 1), hotspot_x=None, hotspot_y=None,
                    ),
                })
        self._active.pop(track_id, None)
        return events


# ---------------------------------------------------------------------------
# Billing Queue Estimator
# ---------------------------------------------------------------------------

class BillingQueueEstimator:
    def __init__(self):
        self._in_zone: dict[int, dict] = {}

    def on_zone_enter(self, track_id: int, visitor_id: str, now: float):
        self._in_zone[track_id] = {
            "visitor_id":   visitor_id,
            "enter_time":   now,
            "joined_queue": False,
        }

    def update(
        self,
        track_id: int,
        store_id: str,
        camera_id: str,
        now: float,
        timestamp: datetime,
    ) -> list[dict]:
        events = []
        info = self._in_zone.get(track_id)
        if info is None:
            return events
        dwell = now - info["enter_time"]
        if not info["joined_queue"] and dwell >= QUEUE_MIN_DWELL:
            info["joined_queue"] = True
            events.append({
                "fn": emit_queue_join,
                "kwargs": dict(
                    visitor_id=info["visitor_id"], track_id=track_id, store_id=store_id,
                    camera_id=camera_id, timestamp=timestamp, queue_length=len(self._in_zone),
                ),
            })
        return events

    def on_zone_exit(
        self,
        track_id: int,
        store_id: str,
        camera_id: str,
        now: float,
        timestamp: datetime,
    ) -> list[dict]:
        events = []
        info = self._in_zone.pop(track_id, None)
        if info is None:
            return events
        dwell = now - info["enter_time"]
        if info["joined_queue"]:
            if dwell <= QUEUE_ABANDON_MAX:
                events.append({
                    "fn": emit_queue_completed,
                    "kwargs": dict(
                        visitor_id=info["visitor_id"], track_id=track_id, store_id=store_id,
                        camera_id=camera_id, timestamp=timestamp, wait_seconds=round(dwell, 1),
                    ),
                })
            else:
                events.append({
                    "fn": emit_queue_abandon,
                    "kwargs": dict(
                        visitor_id=info["visitor_id"], track_id=track_id, store_id=store_id,
                        camera_id=camera_id, timestamp=timestamp, wait_seconds=round(dwell, 1),
                    ),
                })
        return events


# ---------------------------------------------------------------------------
# Per-track state
# ---------------------------------------------------------------------------

class TrackState:
    def __init__(self, track_id: int, visitor_id: str, frame_idx: int, fps: float, bbox: list):
        self.track_id      = track_id
        self.visitor_id    = visitor_id
        self.first_frame   = frame_idx
        self.last_frame    = frame_idx
        self.fps           = fps
        self.is_staff      = False
        self.bbox          = bbox  
        self.prev_y_norm:  Optional[float] = None
        self.emitted_entry = False
        self.emitted_exit  = False
        self.lost_frame_count = 0 
        self.last_seen_timestamp: Optional[datetime] = None

    def dwell_seconds(self) -> float:
        return (self.last_frame - self.first_frame) / max(self.fps, 1.0)


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

def process_video(
    video_path: str,
    store_id: str,
    camera_id: str,
    reid_registry: Optional[ReIDRegistry] = None,
) -> dict:
    if reid_registry is None:
        reid_registry = ReIDRegistry()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps       = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 99999

    # ---- FAIL-SAFE CAMERA CONFIG ROUTING ----
    if camera_id == "entry 2":
        current_conf = 0.70             
        min_gate_dwell = 24             
    elif camera_id == "entry 1":
        current_conf = 0.65             
        min_gate_dwell = 15             
    else:
        current_conf = 0.40             
        min_gate_dwell = 0              

    model     = YOLO(YOLO_MODEL)
    zones     = get_zones_for_camera(store_id, camera_id)
    is_entry  = is_entry_exit_camera(store_id, camera_id)
    is_bill   = is_billing_camera(store_id, camera_id)
    is_stor   = is_storage_camera(store_id, camera_id)

    zone_tracker  = ZoneTracker(zones, fps)
    staff_cls     = StaffClassifier(store_id, camera_id)
    billing_est   = BillingQueueEstimator() if is_bill else None

    active_tracks: dict[int, TrackState] = {}

    frame_idx  = 0
    start_wall = time.time()

    stats = {
        "entries": 0,
        "exits":   0,
        "reentries": 0,
        "staff_detected": 0,
        "frames_processed": 0,
    }

    SKIP = 2

    while frame_idx < total_frames:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
            
        frame_idx += 1
        if frame_idx % SKIP != 0:
            continue

        stats["frames_processed"] += 1
        frame_time_offset = frame_idx / fps
        timestamp = datetime.fromtimestamp(start_wall + frame_time_offset, tz=timezone.utc)

        results = model.track(
            frame, persist=True, conf=current_conf, iou=IOU_THRESHOLD, classes=[0], verbose=False
        )

        observed_track_ids = set()

        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                if box.id is None:
                    continue
                track_id = int(box.id.item())
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1 = max(0, x1); y1 = max(0, y1)
                x2 = min(width, x2); y2 = min(height, y2)
                current_bbox = [x1, y1, x2, y2]

                crop = frame[y1:y2, x1:x2] if y2 > y1 and x2 > x1 else None
                cx_norm = ((x1 + x2) / 2) / width
                cy_norm = ((y1 + y2) / 2) / height

                observed_track_ids.add(track_id)

                if track_id not in active_tracks:
                    matched_lost_id = None
                    best_iou = 0.4  

                    for lost_id, lost_state in active_tracks.items():
                        if lost_id not in observed_track_ids and lost_state.lost_frame_count > 0:
                            iou = _compute_iou(current_bbox, lost_state.bbox)
                            if iou > best_iou:
                                best_iou = iou
                                matched_lost_id = lost_id

                    if matched_lost_id is not None:
                        old_state = active_tracks.pop(matched_lost_id)
                        state = TrackState(track_id, old_state.visitor_id, old_state.first_frame, fps, current_bbox)
                        state.emitted_entry = old_state.emitted_entry
                        state.emitted_exit = old_state.emitted_exit
                        state.is_staff = old_state.is_staff
                        state.prev_y_norm = old_state.prev_y_norm
                        active_tracks[track_id] = state
                    else:
                        is_staff_hint = is_stor   
                        vid, is_reentry, entry_count = reid_registry.match_or_create(crop, time.time(), is_staff_hint)
                        state = TrackState(track_id, vid, frame_idx, fps, current_bbox)
                        state.is_staff = is_staff_hint or reid_registry.is_staff(vid)
                        active_tracks[track_id] = state
                        staff_cls.record_entry(vid, time.time())

                state = active_tracks[track_id]
                state.lost_frame_count = 0
                state.last_frame = frame_idx
                state.bbox = current_bbox
                state.last_seen_timestamp = timestamp
                reid_registry.update_seen(state.visitor_id, time.time())

                # Live staff verification evaluation loops
                in_storage = is_stor   
                is_staff_now = staff_cls.classify(state.visitor_id, track_id, crop, time.time(), in_storage)
                if is_staff_now and not state.is_staff:
                    state.is_staff = True
                    reid_registry.set_staff(state.visitor_id)
                    stats["staff_detected"] += 1

                zone_events = zone_tracker.update(
                    track_id=track_id, visitor_id=state.visitor_id, store_id=store_id,
                    camera_id=camera_id, x_norm=cx_norm, y_norm=cy_norm,
                    frame_idx=frame_idx, timestamp=timestamp
                )
                for ev in zone_events:
                    ev["fn"](**ev["kwargs"])
                    if ev["fn"] == emit_zone_enter and ev["kwargs"].get("is_revenue_zone"):
                        staff_cls.record_revenue_zone(state.visitor_id)

                    if is_bill and billing_est:
                        if ev["fn"] == emit_zone_enter:
                            billing_est.on_zone_enter(track_id, state.visitor_id, time.time())
                        elif ev["fn"] == emit_zone_exit:
                            bev = billing_est.on_zone_exit(track_id, store_id, camera_id, time.time(), timestamp)
                            for b in bev: b["fn"](**b["kwargs"])

                if is_bill and billing_est:
                    bev = billing_est.update(track_id, store_id, camera_id, time.time(), timestamp)
                    for b in bev: b["fn"](**b["kwargs"])

               # === REPAIRED DELAYED ENTRY LIFECYCLE FOR STAFF VALIDATION ===
                if not state.emitted_entry:
                    if is_entry:
                        # Entrance cameras verify against gate constraints immediately
                        if zone_tracker.is_inside_zone_type_verified(track_id, "ENTRY_EXIT", min_gate_dwell):
                            emit_entry(
                                visitor_id=state.visitor_id, store_id=store_id, camera_id=camera_id,
                                timestamp=timestamp, is_staff=state.is_staff, track_id=track_id
                            )
                            stats["entries"] += 1
                            state.emitted_entry = True
                    else:
                        # Interior/Billing cameras: Wait 45 frames (~3 seconds) to let color 
                        # and stationary features calibrate before locking down entry profiles
                        frames_tracked = frame_idx - state.first_frame
                        if frames_tracked >= 45:
                            emit_entry(
                                visitor_id=state.visitor_id, store_id=store_id, camera_id=camera_id,
                                timestamp=timestamp, is_staff=state.is_staff, track_id=track_id
                            )
                            stats["entries"] += 1
                            state.emitted_entry = True
        # ---- Process Lost Tracks ----
        for tid, state in list(active_tracks.items()):
            if tid not in observed_track_ids:
                state.lost_frame_count += SKIP
                
                if state.lost_frame_count > TRACK_MAX_LOST_FRAMES:
                    active_tracks.pop(tid)
                    dwell = state.dwell_seconds()
                    exit_ts = state.last_seen_timestamp if state.last_seen_timestamp else timestamp

                    # CRITICAL FIX ORDER: Read verification fields before triggering flush wipes
                    was_at_gate_verified = zone_tracker.is_inside_zone_type_verified(tid, "ENTRY_EXIT", min_gate_dwell)

                    flush_events = zone_tracker.flush_all(tid, state.visitor_id, store_id, camera_id, state.last_frame, exit_ts)
                    for ev in flush_events:
                        ev["fn"](**ev["kwargs"])
                        if is_bill and billing_est and ev["fn"] == emit_zone_exit:
                            bev = billing_est.on_zone_exit(tid, store_id, camera_id, time.time(), exit_ts)
                            for b in bev: b["fn"](**b["kwargs"])

                    if is_entry and state.emitted_entry and not state.emitted_exit:
                        if was_at_gate_verified:
                            emit_exit(
                                visitor_id=state.visitor_id, store_id=store_id, camera_id=camera_id,
                                timestamp=exit_ts, is_staff=state.is_staff, dwell_seconds=round(dwell, 1), track_id=tid
                            )
                            reid_registry.mark_exit(state.visitor_id, time.time())
                            stats["exits"] += 1
                            state.emitted_exit = True

    # ---- CRITICAL FIX ORDER: Final video boundary cleanup sweep ----
    for tid, state in list(active_tracks.items()):
        dwell = state.dwell_seconds()
        exit_ts = state.last_seen_timestamp if state.last_seen_timestamp else timestamp
        
        # Read the verification matrix coordinates FIRST before clearing memory layouts
        was_at_gate_verified = zone_tracker.is_inside_zone_type_verified(tid, "ENTRY_EXIT", min_gate_dwell)
        zone_tracker.flush_all(tid, state.visitor_id, store_id, camera_id, state.last_frame, exit_ts)
        
        if is_entry and state.emitted_entry and not state.emitted_exit and was_at_gate_verified:
            emit_exit(
                visitor_id=state.visitor_id, store_id=store_id, camera_id=camera_id,
                timestamp=exit_ts, is_staff=state.is_staff, dwell_seconds=round(dwell, 1), track_id=tid
            )
            stats["exits"] += 1
            
    cap.release()
    return stats


def build_arg_parser():
    p = argparse.ArgumentParser(description="Retail Intelligence Video Processor")
    p.add_argument("--video",    required=True, help="Path to video file")
    p.add_argument("--store",    required=True, help="Store ID (store1, store2)")
    p.add_argument("--camera",   required=True,
                   help="Camera ID exactly as in dataset (CAM1..CAM5, entry_clip1, etc.)")
    return p


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    registry = ReIDRegistry()
    stats = process_video(args.video, args.store, args.camera, registry)
    print(f"Done. Stats: {stats}")