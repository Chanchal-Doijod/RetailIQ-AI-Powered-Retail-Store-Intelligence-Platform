# ==============================================================================
# AI ASSISTANCE LOG:
# PROMPT USED: "Optimize YOLOv8 pipeline loop to extract only person detections"
# CHANGES MADE:
# - Restricted detection to COCO class 0 (person)
# - Added reusable function for tracker integration
# - Disabled verbose logging
# ==============================================================================

from ultralytics import YOLO
import cv2


def get_person_detections(frame, model):
    """
    Returns only person detections from the frame.
    """

    results = model(
        frame,
        classes=[0],      # Only person class
        verbose=False,
        imgsz=640
    )[0]

    return results


if __name__ == "__main__":

    model = YOLO("yolov8n.pt")

    video = cv2.VideoCapture("data/videos/CAM 1.mp4")

    while True:

        success, frame = video.read()

        if not success:
            break

        results = get_person_detections(frame, model)

        annotated_frame = results.plot()

        cv2.imshow("Person Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()