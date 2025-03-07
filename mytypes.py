from datetime import datetime
from cv2.typing import MatLike

class Params:
    countdown = 3
    start_time = None
    movement_threshold = 30 # Pixels allowed for movement
    initial_face_position = None
    anti_spoofling = False

    # Define size constraints (30% to 70%)
    max_height = 80
    max_width = 50

    min_height = 40
    min_width = 30


class Colors:
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)


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
    def __init__(self, verified : bool = False, similarity_score : int = None):
        self.verified = verified
        self.similarity_score = similarity_score
