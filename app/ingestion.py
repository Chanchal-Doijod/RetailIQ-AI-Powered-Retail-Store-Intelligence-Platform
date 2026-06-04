import json
import os

EVENT_FILE = "../data/output/events.jsonl"


def save_events(events):

    inserted = 0

    os.makedirs(
        os.path.dirname(EVENT_FILE),
        exist_ok=True
    )

    existing_ids = set()

    if os.path.exists(EVENT_FILE):

        with open(EVENT_FILE, "r") as f:

            for line in f:

                try:
                    event = json.loads(line)

                    existing_ids.add(
                        event["event_id"]
                    )

                except:
                    pass

    with open(EVENT_FILE, "a") as f:

        for event in events:

            if (
                event["event_id"]
                in existing_ids
            ):
                continue

            f.write(
                json.dumps(event)
                + "\n"
            )

            inserted += 1

    return inserted


def get_all_events():

    events = []

    if not os.path.exists(EVENT_FILE):
        return events

    with open(EVENT_FILE, "r") as f:

        for line in f:

            try:

                events.append(
                    json.loads(line)
                )

            except:
                pass

    return events