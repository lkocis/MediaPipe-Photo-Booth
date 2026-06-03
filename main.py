import cv2
import config
import camera as cam  

# --- MOCK FUNKCIJE (Osoba 2, 3 i 4) ---
def mock_detect_face(frame): return {"smile": False, "face_box": (300, 200, 200, 200)} 
def mock_detect_gesture(frame): return {"peace": False, "confidence": 0.9} 
def mock_draw_ui(frame):
    cv2.putText(frame, "Show peace sign to take photo!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.FONT_COLOR, 2, cv2.LINE_AA) 
# --------------------------------------

def main():
    print("Pokretanje Magic Emoji Booth-a...") 
    
    # 1. Inicijalizacija kamere pomoću TVOJIH funkcija
    cap = cam.get_camera()
    cam.setup_camera(cap)
    
    while True:
        # 2. Čitanje framea
        frame = cam.get_frame(cap)
        if frame is None:
            print("Greška: Nije moguće učitati frame.")
            break

        # UI i detekcije
        mock_draw_ui(frame)
        face_data = mock_detect_face(frame) 
        gesture_data = mock_detect_gesture(frame) 

        if face_data["smile"]: pass 
        if gesture_data["peace"]: pass 

        cv2.imshow("Magic Emoji Booth", frame) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Gašenje kamere i čišćenje prozora
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()