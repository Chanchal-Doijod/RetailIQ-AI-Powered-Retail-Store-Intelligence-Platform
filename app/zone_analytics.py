import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

EVENT_FILE = BASE_DIR / "data" / "output" / "events.jsonl"

def get_zone_analytics():

    zone_counts = {}

    try:

        with open(EVENT_FILE, "r") as f:

            for line in f:

                event = json.loads(line)

                zone = event.get("zone_id")

                if zone is None:
                    continue

                zone_counts[zone] = (
                    zone_counts.get(zone, 0) + 1
                )

    except Exception as e:
        return {
            "error": str(e)
        }

    return zone_counts