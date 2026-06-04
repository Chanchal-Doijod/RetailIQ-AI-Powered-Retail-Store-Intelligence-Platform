import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EVENT_FILE = BASE_DIR / "data" / "output" / "events.jsonl"


def get_dwell_analytics():

    zone_dwell = {}
    zone_counts = {}

    total_dwell = 0
    total_events = 0

    try:
        with open(EVENT_FILE, "r") as f:
            for line in f:

                event = json.loads(line)

                if event.get("event_type") != "zone_exited":
                    continue

                dwell = event.get("dwell_seconds", 0)

                if dwell <= 0:
                    continue

                total_dwell += dwell
                total_events += 1

                zone = event.get("zone_id")

                if not zone:
                    continue

                zone_dwell[zone] = zone_dwell.get(zone, 0) + dwell
                zone_counts[zone] = zone_counts.get(zone, 0) + 1

    except Exception as e:
        return {"error": str(e)}

    zone_averages = {}

    for zone in zone_dwell:
        zone_averages[zone] = round(
            zone_dwell[zone] / zone_counts[zone],
            2
        )

    overall_avg = 0

    if total_events:
        overall_avg = round(
            total_dwell / total_events,
            2
        )

    return {
        "avg_dwell_seconds": overall_avg,
        "zones": zone_averages
    }