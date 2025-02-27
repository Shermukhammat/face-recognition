import os, cv2
from uuid import uuid1
from time import sleep
import matplotlib.pyplot as plt



image_path = os.path.join('data', 'images')
number_images = 30


cap = cv2.VideoCapture(0)

for image_num in range(number_images):
    print(f"img num: {image_num}")
    ret, frame = cap.read()
    image_name = os.path.join(image_path, f"{uuid1().hex}.jpg")
    cv2.imwrite(image_name, frame)
    cv2.imshow('frame', frame)
    
    sleep(0.5)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()