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
        #optiiziacija: ako nema emojija za crtanje, ne radimo nepotrebne konverzije slika
        if not self.emoji_particles:
            return
        
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

    #ovdje dodajemo logiku za detekciju osmijeha koristeći MediaPipe, a ne Haar Cascade
    def process_with_mediapipe(self, frame, mp_response):
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time

        #ne treba nam više faces jer to vučemo sada iz MediaPipe rezultata
        
        smiling_people = 0
        smiling_centers = []

        for face in mp_response["all_faces"]:
            x, y, w, h = face["face_box"]

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            #logiku za brojanje osmijeha i centara osmijeha vučemo iz MediaPipe rezultata
            #ostavljamo samo računanje centra lica zbog emojia
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