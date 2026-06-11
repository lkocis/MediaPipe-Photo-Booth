import cv2
import time
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class SmileEmojiDetector:
    def __init__(self):
        self.emoji_particles = []
        self.emojis = ["🎒", "😄", "🤖", "🥳", "✨", "🌈", "🎉"]

        import platform
        if platform.system() == "Windows":
            self.font_path = "C:/Windows/Fonts/seguiemj.ttf"
        elif platform.system() == "Darwin":
            self.font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
        else:  # Linux / Docker
            self.font_path = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
        self.font_cache = {}

        self.last_burst_time = 0
        self.burst_cooldown = 1.0
        self.last_frame_time = time.time()

        self.smile_history = []
        self.history_size = 6
        self.previous_stable_smiling_people = 0

    def get_emoji_font(self):
        if "emoji_base_font" not in self.font_cache:
            last_error = None

            for font_size in (109, 128, 160, 96, 72, 64):
                try:
                    self.font_cache["emoji_base_font"] = ImageFont.truetype(self.font_path, font_size)
                    self.emoji_font_size = font_size
                    break
                except OSError as e:
                    last_error = e
            else:
                raise last_error

        return self.font_cache["emoji_base_font"]

    def get_rendered_emoji(self, emoji, size):
        key = (emoji, size)
        if key in self.font_cache:
            return self.font_cache[key]

        font = self.get_emoji_font()
        canvas_size = self.emoji_font_size + 80
        emoji_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        emoji_draw = ImageDraw.Draw(emoji_layer)

        emoji_draw.text(
            (40, 40),
            emoji,
            font=font,
            embedded_color=True
        )

        bbox = emoji_layer.getbbox()
        if bbox is None:
            return None

        emoji_img = emoji_layer.crop(bbox)
        resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        emoji_img.thumbnail((size, size), resample_filter)

        self.font_cache[key] = emoji_img
        return emoji_img

    def paste_rgba_clipped(self, base, overlay, x, y):
        if overlay is None:
            return

        if x >= base.width or y >= base.height:
            return
        if x + overlay.width <= 0 or y + overlay.height <= 0:
            return

        src_left = max(0, -x)
        src_top = max(0, -y)
        src_right = min(overlay.width, base.width - x)
        src_bottom = min(overlay.height, base.height - y)

        cropped = overlay.crop((src_left, src_top, src_right, src_bottom))
        dst_x = max(0, x)
        dst_y = max(0, y)

        base.alpha_composite(cropped, (dst_x, dst_y))

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
                "vx": random.uniform(-160, 160),
                "vy": random.uniform(-320, -90),
                "size": random.randint(28, 48),
                "life": random.uniform(2.4, 3.4),
                "age": 0.0
            })

    def draw_emojis(self, frame, dt):
        if not self.emoji_particles:
            return
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb).convert("RGBA")

        remaining_particles = []

        for particle in self.emoji_particles:
            particle["age"] += dt

            if particle["age"] < particle["life"]:
                particle["x"] += particle["vx"] * dt
                particle["y"] += particle["vy"] * dt
                particle["vy"] += 420 * dt

                emoji_img = self.get_rendered_emoji(particle["emoji"], particle["size"])
                self.paste_rgba_clipped(
                    pil_image,
                    emoji_img,
                    int(particle["x"]),
                    int(particle["y"])
                )

                remaining_particles.append(particle)

        self.emoji_particles = remaining_particles
        frame[:, :] = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)

    #ovdje dodajemo logiku za detekciju osmijeha koristeći MediaPipe, a ne Haar Cascade
    def process_with_mediapipe(self, frame, mp_response):
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        smiling_people = 0
        smiling_centers = []

        for face in mp_response["all_faces"]:
            x, y, w, h = face["face_box"]

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if face["smile"]:
                smiling_people += 1
                center_x = x + w // 2
                center_y = y + h // 2
                smiling_centers.append((center_x, center_y))
                
                cv2.rectangle(frame, (x+4, y+4), (x + w - 4, y + h - 4), (0, 255, 0), 2)

        self.smile_history.append(smiling_people)
        if len(self.smile_history) > self.history_size:
            self.smile_history.pop(0)

        stable_smiling_people = 0
        for count in [1, 2, 3]:
            if self.smile_history.count(count) >= 3:
                stable_smiling_people = count

        emoji_amount = self.get_emoji_amount(stable_smiling_people)

        # Okidanje eksplozije emojija
        if (stable_smiling_people > 0 
                and stable_smiling_people > self.previous_stable_smiling_people 
                and current_time - self.last_burst_time > self.burst_cooldown):
            
            frame_height, frame_width = frame.shape[:2]
            self.burst_emojis(emoji_amount, frame_width, frame_height, smiling_centers)
            self.last_burst_time = current_time

        self.previous_stable_smiling_people = stable_smiling_people

        self.draw_emojis(frame, dt)

        return {
            "smile": stable_smiling_people > 0,
            "smiling_people": stable_smiling_people
        }