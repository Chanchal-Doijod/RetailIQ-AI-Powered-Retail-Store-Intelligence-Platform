# app/metrics.py
"""
Core metrics calculation.
Conversion Rate = converted_visitors / unique_non_staff_visitors

Conversion is determined by (priority order):
1. queue_completed events (billing queue exit → purchase)
2. POS transaction matched to visitor session (±5 min window)
3. billing_queue_join with no subsequent abandon (implied purchase)
"""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

EVENTS_PATH = Path(
    os.environ.get(
        "EVENTS_OUTPUT",
        str(BASE_DIR / "data" / "output" / "events.jsonl")
    )
)
POS_PATH    = os.environ.get("POS_PATH", "data/resources/pos_transactions.csv")

POS_MATCH_WINDOW = timedelta(minutes=5)


# ---------------------------------------------------------------------------
# Event loader
# ---------------------------------------------------------------------------

def load_events(store_id: Optional[str] = None) -> list[dict]:
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
            sid = ev.get("store_id") or ev.get("store_code")
            if store_id and sid and store_id not in (sid, sid.replace("store_", "store")):
                continue
            events.append(ev)
    return events


# ---------------------------------------------------------------------------
# POS loader
# ---------------------------------------------------------------------------

def load_pos_transactions(store_id: Optional[str] = None) -> list[dict]:
    txns = []
    path = Path(POS_PATH)
    if not path.exists():
        return txns
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("store_id", "")
            if store_id == "store2":
               expected_store = "ST1008"
            else:
              expected_store = store_id
            if expected_store and sid != expected_store:
    
                continue
            txns.append(row)
    return txns


# ---------------------------------------------------------------------------
# Session builder
# ---------------------------------------------------------------------------

def build_visitor_sessions(events: list[dict]) -> dict[str, dict]:
    """
    Returns visitor_id → {
        entry_time, exit_time, is_staff,
        zones_visited, completed_queue, joined_queue, abandoned_queue
    }
    """
    sessions: dict[str, dict] = {}

    def get_vid(ev):
        return ev.get("id_token") or ev.get("visitor_id")

    def parse_ts(ev) -> Optional[datetime]:
        raw = ev.get("event_timestamp") or ev.get("event_time")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    for ev in sorted(events, key=lambda e: e.get("event_timestamp", "")):
        vid  = get_vid(ev)
        etype = ev.get("event_type", "")
        ts    = parse_ts(ev)
        if not vid:
            continue

        if vid not in sessions:
            sessions[vid] = {
                "entry_time":       None,
                "exit_time":        None,
                "is_staff":         ev.get("is_staff", False),
                "zones_visited":    set(),
                "completed_queue":  False,
                "joined_queue":     False,
                "abandoned_queue":  False,
                "reentry_count":    0,
            }

        s = sessions[vid]

        if etype == "entry":
            if s["entry_time"] is None:
                s["entry_time"] = ts
            s["is_staff"] = ev.get("is_staff", s["is_staff"])

        elif etype == "exit":
            s["exit_time"] = ts

        elif etype == "reentry":
            s["reentry_count"] += 1

        elif etype in ("zone_entered", "zone_exited", "zone_dwell"):
            zid = ev.get("zone_id")
            if zid:
                s["zones_visited"].add(zid)

        elif etype == "queue_completed":
            s["completed_queue"] = True

        elif etype == "billing_queue_join":
            s["joined_queue"] = True

        elif etype == "billing_queue_abandon":
            s["abandoned_queue"] = True

    return sessions


# ---------------------------------------------------------------------------
# POS transaction matcher
# ---------------------------------------------------------------------------

def match_pos_to_sessions(
    sessions: dict[str, dict],
    txns: list[dict],
) -> set[str]:
    """
    Returns set of visitor_ids matched to a POS transaction.
    Matches by exit_time ± POS_MATCH_WINDOW.
    """
    converted = set()

    txn_times = []
    for t in txns:
        raw = t.get("transaction_time") or t.get("timestamp") or t.get("date")  or t.get("order_date")
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            txn_times.append(dt)
        except ValueError:
            continue

    if not txn_times:
        return converted

    for vid, sess in sessions.items():
        if sess["is_staff"]:
            continue
        ref_time = sess["exit_time"] or sess["entry_time"]
        if ref_time is None:
            continue
        for tt in txn_times:
            if abs((ref_time - tt).total_seconds()) <= POS_MATCH_WINDOW.total_seconds():
                converted.add(vid)
                break

    return converted


# ---------------------------------------------------------------------------
# Metrics calculator
# ---------------------------------------------------------------------------

def calculate_metrics(store_id: str, window_minutes: int = 60) -> dict:
    events   = load_events(store_id)
    txns     = load_pos_transactions(store_id)
    sessions = build_visitor_sessions(events)

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)

    # Demo mode: include all sessions from events file
    windowed = sessions

    # Unique non-staff visitors
    customer_sessions = {v: s for v, s in windowed.items() if not s["is_staff"]}
    total_visitors    = len(customer_sessions)
    total_staff       = sum(1 for s in windowed.values() if s["is_staff"])

    # Converted visitors (combination approach)
    # Priority 1: queue_completed event
    converted_by_queue = {
        v for v, s in customer_sessions.items() if s["completed_queue"]
    }

    # Priority 2: joined queue + not abandoned (implied purchase)
    converted_implied = {
        v for v, s in customer_sessions.items()
        if s["joined_queue"] and not s["abandoned_queue"]
    }

    # Priority 3: POS matching
    converted_by_pos = match_pos_to_sessions(customer_sessions, txns)

    # Union of all signals
    all_converted = converted_by_queue | converted_implied | converted_by_pos

    converted_count  = len(all_converted)
    conversion_rate  = (
        round(converted_count / total_visitors, 4) if total_visitors > 0 else 0.0
    )

    # Zone funnel
    zone_visits: dict[str, int] = defaultdict(int)
    zone_dwell_totals: dict[str, float] = defaultdict(float)
    for s in customer_sessions.values():
        for zid in s["zones_visited"]:
            zone_visits[zid] += 1

    # Queue metrics
    queue_joins    = sum(1 for s in customer_sessions.values() if s["joined_queue"])
    queue_abandons = sum(1 for s in customer_sessions.values() if s["abandoned_queue"])
    queue_abandon_rate = (
        round(queue_abandons / queue_joins, 4) if queue_joins > 0 else 0.0
    )

    # Reentries
    total_reentries = sum(s["reentry_count"] for s in windowed.values())

    return {
        "store_id":          store_id,
        "window_minutes":    window_minutes,
        "total_visitors":    total_visitors,
        "total_staff":       total_staff,
        "converted_visitors": converted_count,
        "conversion_rate":   conversion_rate,
        "queue_joins":       queue_joins,
        "queue_abandons":    queue_abandons,
        "queue_abandon_rate": queue_abandon_rate,
        "total_reentries":   total_reentries,
        "zone_visit_counts": dict(zone_visits),
        "total_events":      len(events),
        "as_of":             now.isoformat(),
    }
