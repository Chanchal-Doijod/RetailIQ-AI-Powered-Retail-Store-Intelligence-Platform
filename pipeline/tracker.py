# ==============================================================================
# AI ASSISTANCE LOG:
# PROMPT USED: "Create YOLOv8 + ByteTrack person tracking pipeline"
# CHANGES MADE:
# - Integrated reusable detection module
# - Added ByteTrack tracking
# - Added track ID visualization
# - Added tracker safety checks
# ==============================================================================

import cv2
from ultralytics import YOLO
import supervision as sv

from detect import get_person_detections


def run_tracker(video_path):

    model = YOLO("yolov8n.pt")

    tracker = sv.ByteTrack(
        track_activation_threshold=0.25,
        lost_track_buffer=30
    )

    video = cv2.VideoCapture(video_path)

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    while True:

        success, frame = video.read()

        if not success:
            break

        # Step 1: Detect persons
        results = get_person_detections(frame, model)

        # Step 2: Convert YOLO output
        detections = sv.Detections.from_ultralytics(results)

        # Step 3: Track detections
        detections = tracker.update_with_detections(detections)

        labels = []

        if (
            detections.tracker_id is not None
            and len(detections.tracker_id) > 0
        ):

            labels = [
                f"ID:{track_id}"
                for track_id in detections.tracker_id
            ]

            frame = box_annotator.annotate(
                scene=frame,
                detections=detections
            )

            frame = label_annotator.annotate(
                scene=frame,
                detections=detections,
                labels=labels
            )

        cv2.imshow("Retail Tracking Layer", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_tracker("data/videos/CAM 1.mp4")