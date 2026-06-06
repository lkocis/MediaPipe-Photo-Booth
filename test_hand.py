import cv2
from hand_detector import HandDetector

cap = cv2.VideoCapture(0)
detector = HandDetector()

while True:
    success, frame = cap.read()
    if not success: break

    gesture = detector.detect_gesture(frame)

    # Određivanje teksta
    if gesture == "peace":
        text, color = "PEACE!", (0, 0, 255)
    elif gesture == "like":
        text, color = "LIKE!", (255, 0, 0)
    else:
        text, color = "Status: OK", (0, 255, 0)

    cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Hand Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()