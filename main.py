import cv2
import config
import camera as cam  
from hand_detector import HandDetector

# --- MOCK FUNKCIJE (Osoba 2, 3 i 4) ---
def mock_detect_face(frame): return {"smile": False, "face_box": (300, 200, 200, 200)} 
# --------------------------------------

def main():
    print("Pokretanje Magic Emoji Booth-a...") 
    
    # 1. Inicijalizacija kamere pomoću TVOJIH funkcija
    cap = cam.get_camera()
    cam.setup_camera(cap)

    hand_detector = HandDetector()
    
    while True:
        # 2. Čitanje framea
        frame = cam.get_frame(cap)
        if frame is None:
            print("Greška: Nije moguće učitati frame.")
            break

        cv2.putText(frame, "Digni Peace znak ili Like za slikanje!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.FONT_COLOR, 2, cv2.LINE_AA) 
        face_data = mock_detect_face(frame) 
        gesture = hand_detector.detect_gesture(frame) 

        if face_data["smile"]: pass 
        
        if gesture == "peace":
            text, color = "PEACE!", (0, 0, 255)
        elif gesture == "like":
            text, color = "LIKE!", (255, 0, 0)
        else:
            text, color = "Status: OK", (0, 255, 0)

        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Magic Emoji Booth", frame) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()