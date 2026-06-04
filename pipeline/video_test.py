import cv2

video = cv2.VideoCapture("data/videos/CAM 3.mp4")

success, frame = video.read()

print("Video Opened:", success)

if success:
    print("Frame Shape:", frame.shape)

video.release()