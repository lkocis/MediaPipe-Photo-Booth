import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

class HandDetector:
    def __init__(self):
        module_path = os.path.abspath(__file__)
        module_dir = os.path.dirname(module_path)
        model_path = os.path.join(module_dir, 'hand_landmarker.task')
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options, 
            num_hands=1, 
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect_gesture(self, frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        timestamp_ms = int(time.time() * 1000)
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if results.hand_landmarks:
            lm = results.hand_landmarks[0]
            
            # --- VIZUALIZACIJA ---
            connections = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]
            h, w, _ = frame.shape
            points = [(int(p.x * w), int(p.y * h)) for p in lm]
            for s, e in connections: cv2.line(frame, points[s], points[e], (255, 255, 0), 2)
            for x, y in points: cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            # --- LOGIKA ---
            dist = lambda p1, p2: ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5
            
            d_thumb = dist(lm[4], lm[0])
            d_index = dist(lm[8], lm[0])
            d_middle = dist(lm[12], lm[0])
            d_ring = dist(lm[16], lm[0])
            d_pinky = dist(lm[20], lm[0])
            
            # Provjera jesu li prsti savijeni (vrh prsta blizu dlana)
            # Ovo je robusno jer ne ovisi o orijentaciji ruke
            index_down = dist(lm[8], lm[0]) < dist(lm[6], lm[0])
            middle_down = dist(lm[12], lm[0]) < dist(lm[10], lm[0])
            ring_down = dist(lm[16], lm[0]) < dist(lm[14], lm[0])
            pinky_down = dist(lm[20], lm[0]) < dist(lm[18], lm[0])
            
            # PEACE: Indeks i Srednji gore, ostali dolje
            is_like = (d_thumb > 1.4 * d_index) and (d_thumb > 1.4 * d_middle) and \
                      index_down and middle_down and ring_down and pinky_down
            
            # PEACE: Indeks i Srednji su najdalje, ostali savijeni
            is_peace = (d_index > d_thumb and d_middle > d_thumb and d_index > d_ring and d_middle > d_ring) and \
                       ring_down and pinky_down
        
            if is_peace: return "peace"
            if is_like: return "like"
            
        return None