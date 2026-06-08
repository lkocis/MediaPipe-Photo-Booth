import cv2
import time
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class SmileEmojiDetector:
    def __init__(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))

        face_path = os.path.join(module_dir, "haarcascade_frontalface_default.xml")
        smile_path = os.path.join(module_dir, "haarcascade_smile.xml")

        self.face_cascade = cv2.CascadeClassifier(face_path)
        self.smile_cascade = cv2.CascadeClassifier(smile_path)
        
        self.emoji_particles = []
        self.emojis = ["🎒", "😄", "🤖", "🥳", "✨", "🌈", "🎉"]

        self.font_path = "C:/Windows/Fonts/seguiemj.ttf"
        self.font_cache = {}

        self.last_burst_time = 0
        self.burst_cooldown = 1.0
        self.last_frame_time = time.time()

        self.smile_history = []
        self.history_size = 6
        self.previous_stable_smiling_people = 0

    def get_emoji_font(self, size):
        if size not in self.font_cache:
            self.font_cache[size] = ImageFont.truetype(self.font_path, size)
        return self.font_cache[size]

    def get_emoji_amount(self, smiling_people):
        if smiling_people == 1:
            return 10
        elif smiling_people == 2:
            return 25
        elif smiling_people >= 3:
            return 45
        return 0

    def burst_emojis(self, amount, frame_width, frame_height, centers):
        if not centers:
            centers = [(frame_width // 2, frame_height // 2)]

        for _ in range(amount):
            start_x, start_y = random.choice(centers)

            self.emoji_particles.append({
                "emoji": random.choice(self.emojis),
                "x": float(start_x),
                "y": float(start_y),
                "vx": random.uniform(-250, 250),
                "vy": random.uniform(-450, -150),
                "size": random.randint(28, 48),
                "life": random.uniform(1.0, 1.8),
                "age": 0.0
            })

    def draw_emojis(self, frame, dt):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_image)

        remaining_particles = []

        for particle in self.emoji_particles:
            particle["age"] += dt

            if particle["age"] < particle["life"]:
                particle["x"] += particle["vx"] * dt
                particle["y"] += particle["vy"] * dt
                particle["vy"] += 600 * dt

                font = self.get_emoji_font(particle["size"])

                draw.text(
                    (particle["x"], particle["y"]),
                    particle["emoji"],
                    font=font,
                    embedded_color=True
                )

                remaining_particles.append(particle)

        self.emoji_particles = remaining_particles
        frame[:, :] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def process(self, frame):
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=6,
            minSize=(90, 90)
        )

        faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)[:3]

        smiling_people = 0
        smiling_centers = []
        face_boxes = []

        for x, y, w, h in faces:
            face_boxes.append((x, y, w, h))

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            mouth_y1 = y + int(h * 0.60)
            mouth_y2 = y + int(h * 0.92)

            mouth_gray = gray[mouth_y1:mouth_y2, x:x + w]

            if mouth_gray.size == 0:
                continue

            mouth_gray = cv2.equalizeHist(mouth_gray)

            original_h, original_w = mouth_gray.shape[:2]

            normalized_w = 220
            normalized_h = 90
            mouth_resized = cv2.resize(mouth_gray, (normalized_w, normalized_h))

            smiles = self.smile_cascade.detectMultiScale(
                mouth_resized,
                scaleFactor=1.5,
                minNeighbors=15,
                minSize=(25, 12)
            )

            valid_smiles = []

            for sx, sy, sw, sh in smiles:
                if sw > normalized_w * 0.75:
                    continue
                if sh > normalized_h * 0.70:
                    continue
                if sy < normalized_h * 0.20:
                    continue

                valid_smiles.append((sx, sy, sw, sh))

            person_is_smiling = len(valid_smiles) > 0

            if person_is_smiling:
                smiling_people += 1
                smiling_centers.append((x + w // 2, y + h // 2))

                sx, sy, sw, sh = max(valid_smiles, key=lambda s: s[2] * s[3])

                scale_x = original_w / normalized_w
                scale_y = original_h / normalized_h

                sx = int(sx * scale_x)
                sy = int(sy * scale_y)
                sw = int(sw * scale_x)
                sh = int(sh * scale_y)

                cv2.rectangle(
                    frame,
                    (x + sx, mouth_y1 + sy),
                    (x + sx + sw, mouth_y1 + sy + sh),
                    (0, 255, 0),
                    2
                )

        self.smile_history.append(smiling_people)

        if len(self.smile_history) > self.history_size:
            self.smile_history.pop(0)

        stable_smiling_people = 0

        for count in [1, 2, 3]:
            if self.smile_history.count(count) >= 3:
                stable_smiling_people = count

        emoji_amount = self.get_emoji_amount(stable_smiling_people)

        now = time.time()

        if (
            stable_smiling_people > 0
            and stable_smiling_people > self.previous_stable_smiling_people
            and now - self.last_burst_time > self.burst_cooldown
        ):
            frame_height, frame_width = frame.shape[:2]

            self.burst_emojis(
                emoji_amount,
                frame_width,
                frame_height,
                smiling_centers
            )

            self.last_burst_time = now

        self.previous_stable_smiling_people = stable_smiling_people

        self.draw_emojis(frame, dt)

        return {
            "smile": stable_smiling_people > 0,
            "smiling_people": stable_smiling_people,
            "raw_smiling_people": smiling_people,
            "face_boxes": face_boxes,
            "smile_centers": smiling_centers,
            "emoji_amount": emoji_amount
        }