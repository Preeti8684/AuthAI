import cv2

cap = cv2.VideoCapture(0)  # Try 0, 1, or 2 depending on your camera

if not cap.isOpened():
    print("Camera not detected!")
else:
    print("Camera is working!")
    cap.release()
