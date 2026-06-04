import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
import time

from zone_mapper import get_zone_cam1, get_zone_cam2
from detect import get_person_detections
from emit import create_event, save_event


def is_staff(person_crop):

    if person_crop is None or person_crop.size == 0:
        return False

    h, w, _ = person_crop.shape

    torso = person_crop[
        int(h * 0.25):int(h * 0.80),
        :
    ]

    hsv = cv2.cvtColor(
        torso,
        cv2.COLOR_BGR2HSV
    )

    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 30])

    mask = cv2.inRange(
        hsv,
        lower_black,
        upper_black
    )

    black_ratio = (
        np.sum(mask == 255)
        /
        mask.size
    )

    print(
        f"BLACK_RATIO = {black_ratio:.2f}"
    )

    return black_ratio > 0.75

def run_pipeline(
    video_source,
    camera_id,
    store_id="ST1008"
):

    print(f"\nProcessing {camera_id}")

    model = YOLO("yolov8n.pt")

    tracker = sv.ByteTrack(
        track_activation_threshold=0.60,
        lost_track_buffer=180
    )

    video = cv2.VideoCapture(
        video_source
    )

    frame_count = 0

    event_counter = 0

    track_states = {}

    DWELL_INTERVAL = 15

    while True:

        success, frame = video.read()

        if not success:
            break

        frame_count += 1

        if frame_count % 5 != 0:
            continue

        results = get_person_detections(
            frame,
            model
        )

        detections = sv.Detections.from_ultralytics(
            results
        )

        detections = tracker.update_with_detections(
            detections
        )

        if detections.tracker_id is None:
            continue

        current_time = time.time()

        for bbox, track_id in zip(
            detections.xyxy,
            detections.tracker_id
        ):

            x1, y1, x2, y2 = map(
                int,
                bbox
            )

            center_x = int(
                (x1 + x2) / 2
            )

            center_y = int(
                (y1 + y2) / 2
            )

            if camera_id == "CAM_1":

                zone = get_zone_cam1(
                    center_x,
                    center_y
                )

            elif camera_id == "CAM_2":

                zone = get_zone_cam2(
                    center_x,
                    center_y
                )

            else:

                zone = None

            person_crop = frame[
                max(0, y1):min(frame.shape[0], y2),
                max(0, x1):min(frame.shape[1], x2)
            ]

            staff_flag = is_staff(
                person_crop
            )

            color = (
                (0, 0, 255)
                if staff_flag
                else (0, 255, 0)
            )

            label = (
                f"STAFF {track_id}"
                if staff_flag
                else f"CUSTOMER {track_id}"
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

            if staff_flag:
                continue

            # First time customer detected
            if track_id not in track_states:

                track_states[track_id] = {

                    "first_seen":
                    current_time,

                    "last_dwell":
                    current_time,

                    "zone":
                    zone
                }

                entry_event = create_event(
                    visitor_id=str(track_id),
                    event_type="ENTRY",
                    camera_id=camera_id,
                    store_id=store_id,
                    confidence=1.0
                )

                save_event(
                    entry_event
                )

                zone_event = create_event(
                    visitor_id=str(track_id),
                    event_type="ZONE_ENTER",
                    camera_id=camera_id,
                    store_id=store_id,
                    zone_id=zone,
                    confidence=1.0
                )

                save_event(
                    zone_event
                )

                event_counter += 2

                print(
                    f"ENTRY -> Customer {track_id}"
                )

                print(
                    f"ZONE_ENTER -> {zone}"
                )

            else:

                elapsed = (
                    current_time
                    -
                    track_states[track_id]["last_dwell"]
                )

                if elapsed >= DWELL_INTERVAL:

                    dwell_event = create_event(
                        visitor_id=str(track_id),
                        event_type="ZONE_DWELL",
                        camera_id=camera_id,
                        store_id=store_id,
                        zone_id=zone,
                        dwell_ms=int(
                            elapsed * 1000
                        ),
                        confidence=1.0
                    )

                    save_event(
                        dwell_event
                    )

                    track_states[track_id][
                        "last_dwell"
                    ] = current_time

                    event_counter += 1

                    print(
                        f"DWELL -> Customer {track_id}"
                    )

        cv2.imshow(
            camera_id,
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()

    cv2.destroyAllWindows()

    print("\nProcessing Complete")

    print(
        f"Tracked IDs: "
        f"{len(track_states)}"
    )

    print(
        f"Events Written: "
        f"{event_counter}"
    )


if __name__ == "__main__":

    run_pipeline(
        video_source="data/videos/CAM 2.mp4",
        camera_id="CAM_2"
    )