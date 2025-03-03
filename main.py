import cv2, os 
from deepface import DeepFace
from cv2.typing import MatLike
from data import DataBase, User
from datetime import datetime, timedelta
from time import sleep

class Colors:
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)


class Params:
    countdown = 3
    start_time = None
    movement_threshold = 30 # Pixels allowed for movement
    initial_face_position = None
    anti_spoofling = True

    # Define size constraints (30% to 70%)
    max_height = 80
    max_width = 50

    min_height = 40
    min_width = 30

class Face:
    def __init__(self, x: int, y: int, w: int, h: int, is_real : bool = True):
        if not all(isinstance(i, int) for i in [x, y, w, h]):
            raise TypeError("Face: All parameters must be integers")
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_real = is_real

    @property
    def x2(self) -> int:
        return self.x + self.w
    
    @property
    def y2(self) -> int:
        return self.y + self.h
    
    def moved_too_much(self) -> bool:
        """Check if the face moved significantly"""
        if Params.initial_face_position is None:
            Params.initial_face_position = (self.x, self.y)
            Params.start_time = datetime.now()
            Params.countdown = 3
            return False
        
        elif Params.countdown <= 0:
            return False
        
        x1, y1 = Params.initial_face_position

        if abs(x1 - self.x) > Params.movement_threshold or abs(y1 - self.y) > Params.movement_threshold:
            Params.initial_face_position = (self.x, self.y)
            Params.countdown = 3
            return True
        
        return False
    

    def size_to_large(self, frame : MatLike) -> bool:
        frame_height, frame_width, _ = frame.shape
        face_width = (self.w / frame_width) * 100
        face_height = (self.h / frame_height) * 100

        return (Params.max_width < face_width) or (Params.max_height < face_height)

    def size_to_small(self, frame : MatLike) -> bool:
        frame_height, frame_width, _ = frame.shape
        face_width = (self.w / frame_width) * 100
        face_height = (self.h / frame_height) * 100

        return (Params.min_width > face_width) or (Params.min_height >face_height)
    


class VerificationResolt:
    def __init__(self, verified : bool = False):
        self.verified = verified
        # DeepFace.verify()
        

class FaceRecognizer:
    def __init__(self, camera : int = 0):
        self.cap = cv2.VideoCapture(camera)
        self.extract_faces : function = None
        self.find_face : function = None
        self.verify_face : function = None
        self.frame_name : str = "Face Id"
    
    def start(self):
        skeep = False
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # if skeep:
            #     skeep = False
            #     continue
            # else:
            #     skeep = True
            
            faces : list[Face] = self.extract_faces(frame)
            if len(faces) == 1:
                face = faces[0]
                
                if not face.is_real and Params.anti_spoofling:
                    Params.initial_face_position = None
                    if not show(frame, self.frame_name):
                        break

                elif face.size_to_large(frame):
                    if not show(frame, self.frame_name):
                        break

                elif face.size_to_small(frame):
                    if not show(frame, self.frame_name, face=face, text = "Yaqinroq keling", color = Colors.RED):
                        break
                    
                elif face.moved_too_much():
                    if not show(frame, self.frame_name):
                        break
                
                elif Params.countdown <= 0:
                    if not show(frame, self.frame_name, face = face, text = f'Aniqlanmoqda'):
                        break

                    Params.initial_face_position = None
                    ret, new_frame = self.cap.read()
                    if not ret:
                        break

                    users : list[User] = self.find_face(frame, face)
                    if users:
                        if not check_faces(frame = frame, face = face, new_frame = new_frame, users = users, frame_name = self.frame_name):
                            break
                    
                    else:
                        if not show(new_frame, self.frame_name, face = face, text = "Ro'yxatdan o'tmagan", color = Colors.RED):
                            break
                    sleep(5)
                           
                else:
                    start_time = Params.start_time if Params.start_time else datetime.now()
                    elapsed_time = datetime.now() - start_time
                    if elapsed_time >= timedelta(seconds=1):
                        Params.countdown -= 1
                        Params.start_time = datetime.now()
            
                    if not self.show(frame, face = face, text = f'Qimirlamay turing {Params.countdown}'):
                        break
                
            elif not self.show(frame):
                break
    
    def show(self, frame : MatLike, 
             face : Face = None, 
             text : str = None,
             text_color : tuple[int] = Colors.BLUE,
             rectangle_color : tuple[int] = Colors.BLUE) -> bool:
        
        if isinstance(face, Face):
            cv2.rectangle(frame, (face.x, face.y), (face.x2, face.y2), rectangle_color, 2)
            if text:
                cv2.putText(frame, text, (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        cv2.imshow(self.frame_name, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False
        
        return True

    def extract_faces_handler(self):
        def wrapper(fun):
            self.extract_faces = fun
        return wrapper

    def find_face_handler(self):
        def wrapper(fun):
            self.find_face = fun
        return wrapper
    
    def verify_face_handler(self):
        def wrapper(fun):
            self.verify_face = fun
        return wrapper


def check_faces(frame : MatLike = None, new_frame : MatLike = None, face : Face = None, users : list[User] = [], frame_name : str = None) -> bool:
    status = True
    found : bool = False

    for user in users:
        res = verify_face(frame, face, user)
        if res.verified:
            status = show(new_frame, frame_name, face = face, text = f'{user.name}', color = Colors.GREEN)
            found = True
            break

    if not found:
        show(new_frame, frame_name, face = face, text = "Ro'yxatdan o'tmagan", color = Colors.RED)

    return status

def show(frame : MatLike, frame_name : str,
         face : Face = None, 
         text : str = None,
         color : tuple[int] = Colors.BLUE) -> bool:
        
    if isinstance(face, Face):
        cv2.rectangle(frame, (face.x, face.y), (face.x2, face.y2), color, 2)
        if text:
            cv2.putText(frame, text, (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
    cv2.imshow(frame_name, frame)
        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return False        
    return True


fr = FaceRecognizer()
db = DataBase('data/data.sqlite')


@fr.extract_faces_handler()
def extract_faces(frame : MatLike) -> list[Face]:
    faces = DeepFace.extract_faces(frame, detector_backend='ssd', enforce_detection=False, anti_spoofing=True)
    resolt = []
    for face in faces:
        region = face["facial_area"]  # Get bounding box
        is_real = face.get('is_real') # Is face real or not
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]

        resolt.append(Face(x = x, y = y, w = w, h = h, is_real = is_real))
    return resolt

@fr.find_face_handler()
def find_face(frame : MatLike, face : Face) -> list[User]:
    face_frame = frame[face.y:face.y2, face.x:face.x2]  # Crop the face
    
    users = []
    results = DeepFace.find(face_frame, db_path="./data/images", enforce_detection=False, silent=True)
    for result in results:
        if result.empty:
            continue
        
        identity = result['identity'].iloc[0]
        filename = os.path.basename(identity)
        file_key : str = os.path.splitext(filename)[0]
        if file_key.isnumeric():
            user = db.get_user(int(file_key))
            if user:
                users.append(user)
    return users


def verify_face(frame : MatLike, face : Face, user : User) -> VerificationResolt:
    face_frame = frame[face.y:face.y2, face.x:face.x2]  # Crop the face
    
    if not os.path.exists(user.photo_path):
        print(f"user id: {user.id}, {user.photo_path} not exsit")

    resolt = DeepFace.verify(face_frame, user.photo_path, 
                             anti_spoofing = False, 
                             model_name = 'ArcFace',
                             enforce_detection = False)
    if isinstance(resolt, dict):
        verified = resolt.get('verified', False)
        return VerificationResolt(verified = verified)

    return VerificationResolt()

if __name__ == '__main__':
    fr.start()