import cv2, os, sys
from .types import Params, Face, VerifyResolt, Resolt, Colors
from cv2.typing import MatLike
from deepface import DeepFace
from data import User, DataBase
from .utilites import resource_path
from . import utilites


class FaceRecognizer:
    def __init__(self, camera : int = 0, db : DataBase = None):
        self.cap = cv2.VideoCapture(camera)
        self.db = db


    def extract_faces(self, frame : MatLike) -> list[Face]:
        faces = DeepFace.extract_faces(frame, detector_backend='ssd', enforce_detection=False)
        resolt = []
        for face in faces:
            region = face["facial_area"]  # Get bounding box
            is_real = face.get('is_real', True) # Is face real or not
            x, y, w, h = region["x"], region["y"], region["w"], region["h"]

            resolt.append(Face(x = x, y = y, w = w, h = h, is_real = is_real))
        return resolt


    def find_face(self, frame : MatLike, face : Face) -> list[User]:
        face_frame = frame[face.y:face.y2, face.x:face.x2]  # Crop the face
    
        users = []
        results = DeepFace.find(face_frame, db_path=resource_path("data/images"), enforce_detection=False, silent=True, refresh_database = True)
        for result in results:
            if result.empty:
                continue
        
            identity = result['identity'].iloc[0]
            filename = os.path.basename(identity)
            file_key : str = os.path.splitext(filename)[0]
            if file_key.isnumeric():
                user = self.db.get_user(int(file_key))
                if user:
                    users.append(user)
        return users


    def verify_face(self, frame : MatLike, face : Face, user : User) -> VerifyResolt:
        face_frame = frame[face.y:face.y2, face.x:face.x2]  # Crop the face
    
        if not os.path.exists(user.photo_path):
            print(f"user id: {user.id}, {user.photo_path} not exsit")

        result = DeepFace.verify(face_frame, user.photo_path, 
                             anti_spoofing = False, 
                             model_name = 'ArcFace',
                             enforce_detection = False)

    
        if isinstance(result, dict):
            similarity_score = 1 - (result["distance"] / result["threshold"]) 
            # print('similarity_score:', similarity_score)
            # verified = True if similarity_score > 0.5 else False
            verified = result.get('verified', False)
            return VerifyResolt(verified = verified, similarity_score=similarity_score)

        return VerifyResolt()



