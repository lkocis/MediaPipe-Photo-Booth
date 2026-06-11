import os
import cv2
import config
import numpy as np
from hand_detector import HandDetector
from face_detection import detect_face
import time
from flask import Flask, Response, render_template_string, request, jsonify
import threading
import base64
from smile_emoji import SmileEmojiDetector

app = Flask(__name__)
hand_detector = HandDetector()
smile_emoji_detector = SmileEmojiDetector()

output_frame = None
frame_lock = threading.Lock()
last_result = {"text": "Status: OK", "color": [0, 255, 0], "smile": False}

photos_dir = config.PHOTOS_DIR
if not os.path.exists(photos_dir):
    os.makedirs(photos_dir)

close_photo_at = 0
photo_blocked = False

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Photo Booth</title>
    <style>
        body { background: #111; display: flex; flex-direction: column;
               justify-content: center; align-items: center; 
               height: 100vh; margin: 0; color: white; font-family: Arial; }
        #canvas { display: none; }
        #overlay { font-size: 24px; margin-top: 10px; }
        video { border: 3px solid #444; max-width: 100%; }
    </style>
</head>
<body>
    <video id="video" width="1280" height="720" autoplay playsinline></video>
    <canvas id="canvas" width="1280" height="720"></canvas>
    <div id="overlay">Učitavanje kamere...</div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const overlay = document.getElementById('overlay');

        // Pokreni kameru
        navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
            .then(stream => {
                video.srcObject = stream;
                video.play();
                setInterval(sendFrame, 100); // šalji frame svakih 100ms
            })
            .catch(err => {
                overlay.textContent = 'Greška kamere: ' + err.message;
            });

        async function sendFrame() {
            ctx.drawImage(video, 0, 0, 1280, 720);
            const base64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

            try {
                const res = await fetch('/process_frame', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ frame: base64 })
                });
                const data = await res.json();
                overlay.textContent = data.text + (data.smile ? ' 😊' : '');
                overlay.style.color = `rgb(${data.color[2]}, ${data.color[1]}, ${data.color[0]})`;
                
                if (data.saved) {
                    overlay.textContent = '📸 FOTOGRAFIJA SPREMLJENA!';
                }
            } catch(e) {
                console.error(e);
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/process_frame", methods=["POST"])
def process_frame():
    global close_photo_at, photo_blocked

    data = request.get_json()
    img_data = base64.b64decode(data["frame"])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"text": "Greška frame-a", "color": [0, 0, 255], "smile": False, "saved": False})

    current_time = time.time()

    # Odblokiraj nakon 3 sekunde
    if photo_blocked and current_time >= close_photo_at:
        photo_blocked = False

    # Detekcija lica
    mp_face_response = detect_face(frame)
    face_status = smile_emoji_detector.process_with_mediapipe(frame, mp_face_response)
    smile = face_status["smile"]

    saved = False

    if not photo_blocked:
        gesture = hand_detector.detect_gesture(frame)

        if gesture == "peace":
            text, color = "PEACE!", [0, 0, 255]
        elif gesture == "like":
            text, color = "LIKE!", [255, 0, 0]
        else:
            text, color = "Status: OK", [0, 255, 0]

        if gesture in ("peace", "like"):
            filename = f"photo_{int(time.time())}.jpg"
            filepath = os.path.join(photos_dir, filename)
            cv2.imwrite(filepath, frame)
            print(f"[PHOTO BOOTH] Slika spremljena: {filepath}")
            close_photo_at = current_time + 3.0
            photo_blocked = True
            saved = True
    else:
        text, color = "📸 FOTOGRAFIJA SPREMLJENA!", [0, 255, 255]

    return jsonify({
        "text": text,
        "color": color,
        "smile": smile,
        "saved": saved
    })

if __name__ == "__main__":
    print("Pokretanje Photo Booth-a...")
    print("Otvori browser na: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)