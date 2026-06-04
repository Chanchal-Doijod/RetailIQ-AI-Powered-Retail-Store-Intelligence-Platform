# app/funnel.py
"""
Shopper funnel:
  Entered → Browsed (entered any zone) → Queue (billing_queue_join)
  → Converted (queue_completed or POS match)

Drop-off is calculated between each consecutive stage.
"""

from app.metrics import (
    load_events,
    load_pos_transactions,
    build_visitor_sessions,
    match_pos_to_sessions,
)
from collections import defaultdict


FUNNEL_STAGES = [
    "entered_store",
    "browsed_zone",
    "reached_billing",
    "converted",
]


def calculate_funnel(store_id: str) -> dict:
    events   = load_events(store_id)
    txns     = load_pos_transactions(store_id)
    sessions = build_visitor_sessions(events)

    customers = {v: s for v, s in sessions.items() if not s["is_staff"]}
    total = len(customers)
    if total == 0:
        return {
            "store_id": store_id,
            "stages":   {s: 0 for s in FUNNEL_STAGES},
            "drop_offs": {},
            "drop_off_rates": {},
        }

    browsed = {
        v for v, s in customers.items() if len(s["zones_visited"]) > 0
    }

    reached_billing = {
        v for v, s in customers.items() if s["joined_queue"] or s["completed_queue"]
    }

    converted_queue = {v for v, s in customers.items() if s["completed_queue"]}
    converted_implied = {
        v for v, s in customers.items()
        if s["joined_queue"] and not s["abandoned_queue"]
    }
    converted_pos = match_pos_to_sessions(customers, txns)
    converted = converted_queue | converted_implied | converted_pos

    stages = {
        "entered_store":   total,
        "browsed_zone":    len(browsed),
        "reached_billing": len(reached_billing),
        "converted":       len(converted),
    }

    stage_keys  = FUNNEL_STAGES
    drop_offs   = {}
    drop_off_rates = {}
    for i in range(len(stage_keys) - 1):
        curr_key = stage_keys[i]
        next_key = stage_keys[i + 1]
        drop_key = f"{curr_key}_to_{next_key}"
        curr_count = stages[curr_key]
        next_count = stages[next_key]
        drop = curr_count - next_count
        drop_offs[drop_key]      = drop
        drop_off_rates[drop_key] = round(drop / curr_count, 4) if curr_count > 0 else 0.0

    # Zone-level drop-off: which zones get attention but not sales
    zone_visit_counts: dict[str, int] = defaultdict(int)
    zone_converted_counts: dict[str, int] = defaultdict(int)
    for vid, s in customers.items():
        for zid in s["zones_visited"]:
            zone_visit_counts[zid] += 1
            if vid in converted:
                zone_converted_counts[zid] += 1

    zone_conversion = {}
    for zid, visits in zone_visit_counts.items():
        conv = zone_converted_counts.get(zid, 0)
        zone_conversion[zid] = {
            "visits":          visits,
            "converted":       conv,
            "conversion_rate": round(conv / visits, 4) if visits > 0 else 0.0,
            "drop_off_rate":   round((visits - conv) / visits, 4) if visits > 0 else 0.0,
        }

    # Zones with high visits but low conversion
    attention_no_sales = {
        zid: info for zid, info in zone_conversion.items()
        if info["visits"] >= 3 and info["conversion_rate"] < 0.1
    }

    return {
        "store_id":          store_id,
        "stages":            stages,
        "drop_offs":         drop_offs,
        "drop_off_rates":    drop_off_rates,
        "zone_conversion":   zone_conversion,
        "attention_no_sales": attention_no_sales,
    }
