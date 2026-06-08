import cv2
import config

def get_camera():
    return cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
    
def setup_camera(camera):
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

def get_frame(camera):
    success, frame = camera.read()
    if not success or frame is None:
        return None
    
    # Ogledalo efekt (flip) - za prirodan UX 
    frame = cv2.flip(frame, 1)
    return frame