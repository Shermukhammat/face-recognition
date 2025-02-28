import cv2
import cv2.data
from datetime import datetime, timedelta
from deepface import DeepFace
import pandas as pd
from time import sleep
import os


data = {
    '1': "Shermuhammad",
    '2': "Jenifer",
    '3': "Temur",
    '4': "Mehriddin",
    '5': "O'lmas",
    '6': "Musk"
}

red = (0, 0, 255)
green = (0, 255, 0)
blue = (255, 0, 0)
yellow = (0, 255, 255)
white = (255, 255, 255)

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(0)
frame_skip = 3
frame_count = 0
countdown = 3
start_time = None
movement_threshold = 30 # Pixels allowed for movement
initial_face_position = None

# Define size constraints (30% to 70%)
min_size_percentage = 40
max_size_percentage = 70
min_size_percentage2 = 20
max_size_percentage2 = 30
freeze = False

def face_moved_too_much(initial, current):
    """Check if the face moved significantly"""
    if initial is None:
        return False
    x1, y1, w1, h1 = initial
    x2, y2, w2, h2 = current
    return abs(x1 - x2) > movement_threshold or abs(y1 - y2) > movement_threshold

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frames for better performance

    # Get frame size
    frame_height, frame_width, _ = frame.shape

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Process each detected face
    if len(faces) > 0:
        x, y, w, h = faces[0] 

    
        
        # Calculate face size as a percentage of frame size
        face_width_percentage = (w / frame_width) * 100
        face_height_percentage = (h / frame_height) * 100
    
        # Check if the face size is within the desired range
        if (min_size_percentage <= face_width_percentage <= max_size_percentage) and \
           (min_size_percentage <= face_height_percentage <= max_size_percentage):
            
            if initial_face_position is None:
                initial_face_position = (x, y, w, h)
                start_time = datetime.now()

            if face_moved_too_much(initial_face_position, (x, y, w, h)):
                countdown = 3  # Reset countdown if face moves
                start_time = datetime.now()
                initial_face_position = (x, y, w, h)

            # Countdown logic
            elapsed_time = datetime.now() - start_time
            if elapsed_time >= timedelta(seconds=1):
                countdown -= 1
                start_time = datetime.now()

            # Draw rectangle around the face
            if countdown == 0:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"Aniqlanmoqda ...", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                cv2.imshow("Face Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                initial_face_position = None
                countdown = 3

                face = frame[y:y+h, x:x+w]  # Crop the face
                results = DeepFace.find(face, db_path="./db", enforce_detection=False, silent=True)
    
                if results and not results[0].empty:
                    best_match = results[0].iloc[0]
                    identity = best_match['identity']
        
                    # Proper filename extraction
                    filename = os.path.basename(identity)
                    file_key = os.path.splitext(filename)[0]
        
                    text = data.get(file_key, "Ro'yxatdan o'tmagan")
                    if text == "Ro'yxatdan o'tmagan":
                        color = red
                    else:
                        color = green
                    
                    text += f" {1 - best_match['distance']:.2f} %"
                    # Reset counters
                    initial_face_position = None
                    
                else:
                    color = red
                    text = f"Ro'yxatdan o'tmagan"
                
          
                ret, frame = cap.read()
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.imshow("Face Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                sleep(5)

            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"Qimrlamay turing {countdown}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            

        elif (min_size_percentage2 <= face_width_percentage <= max_size_percentage) and \
           (min_size_percentage2 <= face_height_percentage <= max_size_percentage):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, "Yaqinroq keling", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # Display the frame
    cv2.imshow("Face Detection", frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()