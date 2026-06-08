import os
import cv2
import config
import camera as cam  
from hand_detector import HandDetector
from smile_emoji import SmileEmojiDetector
from face_detection import detect_face  
import time

def main():
    print("Pokretanje Photo Booth-a...") 

    if not os.path.exists(config.PHOTOS_DIR):
        os.makedirs(config.PHOTOS_DIR)
    
    cap = cam.get_camera()
    cam.setup_camera(cap)

    smile_detector = SmileEmojiDetector()
    hand_detector = HandDetector()
    
    close_photo_window_at = 0
    photo_window_open = False
    last_photo_path = None

    while True:
        current_time = time.time()
        
        if photo_window_open and current_time >= close_photo_window_at:
            cv2.destroyWindow("[PHOTO BOOTH] Uslikana fotografija")
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

        face_status = smile_detector.process_with_mediapipe(frame, mp_face_response)

        # Provjera osmijeha preko novog sustava
        if face_status["smile"]: 
            cv2.putText(frame, "OSMIJEH DETEKTIRAN!", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, (0, 255, 255), 2, cv2.LINE_AA)
        
        if not photo_window_open:
            cv2.putText(frame, "Digni Peace znak ili Like za slikanje!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.FONT_COLOR, 2, cv2.LINE_AA) 
            
            gesture = hand_detector.detect_gesture(frame) 
            
            if gesture == "peace":
                text, color = "PEACE!", (0, 0, 255)
            elif gesture == "like":
                text, color = "LIKE!", (255, 0, 0)
            else:
                text, color = "Status: OK", (0, 255, 0)
                
            if gesture == "peace" or gesture == "like":
                filename = f"photo_{int(time.time())}.jpg"
                filepath = os.path.join(config.PHOTOS_DIR, filename)
                
                cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                cv2.imwrite(filepath, frame)
                last_photo_path = filepath
                print(f"[PHOTO BOOTH] Slika uspješno spremljena: {filepath}")
                
                popup_frame = frame.copy()
                cv2.putText(popup_frame, "FOTOGRAFIJA SPREMLJENA!", (30, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                
                cv2.imshow("[PHOTO BOOTH] Uslikana fotografija", popup_frame)
                
                close_photo_window_at = current_time + 3.0
                photo_window_open = True
        else:
            cv2.putText(frame, "Slikanje blokirano (prikaz slike u tijeku...)", (30, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, (0, 0, 255), 2, cv2.LINE_AA)
            text, color = "BLOCKED", (0, 0, 255)

        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("[PHOTO BOOTH] Photo Booth", frame) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()