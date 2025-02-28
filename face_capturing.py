import cv2
import os
from deepface import DeepFace
from time import sleep
from datetime import datetime, timedelta

# Ensure the 'db' folder exists
DB_PATH = "db"
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

cap = cv2.VideoCapture(0)
images_count = 10
record_count = 0
next_record_time = datetime.now() + timedelta(seconds=10)


while record_count < images_count:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        faces = DeepFace.extract_faces(frame, detector_backend = "opencv", enforce_detection = False)

        if next_record_time + timedelta(seconds=5) < datetime.now():
            for face in faces:
                if record_count >= images_count:
                    break

                facial_area = face["facial_area"]
                x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]
                # Extract face region
                face_img = frame[y:y+h, x:x+w]

                if face_img.shape[0] > 0 and face_img.shape[1] > 0:
                    # Use a valid filename format (no slashes or colons)
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    img_path = f"{DB_PATH}/face_{timestamp}_{record_count}.jpg"
                
                    cv2.imwrite(img_path, face_img)
                    print(f"Saved: {img_path}")

                    next_record_time += timedelta(seconds=5)
                
                    record_count += 1

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"Recor {record_count}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                sleep(0.5)
        
        else:
            for face in faces:
                facial_area = face["facial_area"]
                x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]
                # Extract face region
                face_img = frame[y:y+h, x:x+w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    
    except Exception as e:
        print(f"Error detecting face: {e}")

    cv2.imshow("Face Detection", frame)
  
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
