import cv2
import mediapipe as mp
import time
from mediapipe.tasks.python import vision

#mediapipe detektori
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="./face_landmarker.task"),
    running_mode=VisionRunningMode.VIDEO,
    output_face_blendshapes=True,
    num_faces=4  
)

detector = vision.FaceLandmarker.create_from_options(options)

#funckija obrađuje svaki frame iz main funkcije
#vraća True/False ako je osoba nasmijana ili ne
# i vraća "face_box": (x, y, w, h)

def detect_face(frame):

    h, w, _ = frame.shape

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )

    timestamp = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp)

    response = {
        "smile": False,
        "face_box": (0, 0, 0, 0),  # Ili None, ovisno što Osoba 4 preferira
        "all_faces": []
    }

    if result.face_landmarks and result.face_blendshapes:

        for i in range(len(result.face_landmarks)):
            face_landmarks = result.face_landmarks[i]
            face_blendshapes = result.face_blendshapes[i]

            smile_left = 0.0
            smile_right = 0.0

            for blendshape in face_blendshapes:
                if blendshape.category_name == "mouthSmileLeft":
                    smile_left = blendshape.score
                elif blendshape.category_name == "mouthSmileRight":
                    smile_right = blendshape.score

            mean_smile = (smile_left + smile_right)/2.0
            is_smiling = mean_smile > 0.45

            if is_smiling:
                response["smile"] = True
            
            # računamo face box 
            x_coords = [lm.x for lm in face_landmarks]
            y_coords = [lm.y for lm in face_landmarks]
            
            min_x = int(min(x_coords) * w)
            max_x = int(max(x_coords) * w)
            min_y = int(min(y_coords) * h)
            max_y = int(max(y_coords) * h)
            
            box_w = max_x - min_x
            box_h = max_y - min_y
            current_box = (min_x, min_y, box_w, box_h)
            
            if i == 0:
                response["face_box"] = current_box
                
            response["all_faces"].append({
                "face_box": current_box,
                "smile": is_smiling
            })

    return response
