import os
import cv2
import config
import camera as cam
from hand_detector import HandDetector
from face_detection import detect_face
import time
from flask import Flask, Response, render_template_string
import threading

app = Flask(__name__)

output_frame = None
frame_lock = threading.Lock()

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Photo Booth</title>
    <style>
        body { background: #111; display: flex; justify-content: center; 
               align-items: center; height: 100vh; margin: 0; }
        img { max-width: 100%; border: 3px solid #444; }
    </style>
</head>
<body>
    <img src="/video_feed">
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

def generate_frames():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                continue
            _, buffer = cv2.imencode(".jpg", output_frame)
            frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def main():
    global output_frame
    print("Pokretanje Photo Booth-a...")

    if not os.path.exists(config.PHOTOS_DIR):
        os.makedirs(config.PHOTOS_DIR)

    # Pokreni Flask u pozadinskom threadu
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    print("Web stream dostupan na: http://localhost:5000")

    cap = cam.get_camera()
    cam.setup_camera(cap)

    hand_detector = HandDetector()

    close_photo_window_at = 0
    photo_window_open = False
    last_photo_path = None

    while True:
        current_time = time.time()

        if photo_window_open and current_time >= close_photo_window_at:
            photo_window_open = False
            if last_photo_path and os.path.exists(last_photo_path):
                os.remove(last_photo_path)
                last_photo_path = None
                print("[PHOTO BOOTH] Slika obrisana. Ponovno omogućeno slikanje!")
            else:
                print("[PHOTO BOOTH] Prozor zatvoren. Ponovno omogućeno slikanje!")

        frame = cam.get_frame(cap)
        if frame is None:
            print("Greška: Nije moguće učitati frame.")
            break

        mp_face_response = detect_face(frame)

        if mp_face_response["smile"]:
            cv2.putText(frame, "OSMIJEH DETEKTIRAN!", (30, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, (0, 255, 255), 2)

        if not photo_window_open:
            cv2.putText(frame, "Digni Peace ili Like za slikanje!", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.FONT_COLOR, 2)

            gesture = hand_detector.detect_gesture(frame)

            if gesture == "peace":
                text, color = "PEACE!", (0, 0, 255)
            elif gesture == "like":
                text, color = "LIKE!", (255, 0, 0)
            else:
                text, color = "Status: OK", (0, 255, 0)

            if gesture in ("peace", "like"):
                filename = f"photo_{int(time.time())}.jpg"
                filepath = os.path.join(config.PHOTOS_DIR, filename)
                cv2.imwrite(filepath, frame)
                last_photo_path = filepath
                print(f"[PHOTO BOOTH] Slika spremljena: {filepath}")
                close_photo_window_at = current_time + 3.0
                photo_window_open = True
        else:
            text, color = "BLOCKED", (0, 0, 255)
            cv2.putText(frame, "Slikanje blokirano...", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, (0, 0, 255), 2)

        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        with frame_lock:
            output_frame = frame.copy()

    cap.release()

if __name__ == "__main__":
    main()