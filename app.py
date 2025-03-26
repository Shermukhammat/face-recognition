from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QFont
from styles import main_gui_style
from recognizer import FaceRecognizer
from recognizer.types import Face, VerifyResolt, Colors, Params
from recognizer.utilites import wrong, correct, camera, resource_path
from data import DataBase, User
from cv2.typing import MatLike
from datetime import datetime, timedelta
import cv2, sys, os



class FaceIdApp(QWidget):
    def __init__(self, title: str = "Yo`qlamachi"):
        super().__init__()
        self._init_ui(title)
        self._create_media_components()
        self._create_info_panel()
        self._create_control_buttons()
        self._setup_layouts()
        self._init_video()
        self._connect_signals()
        
        # Video recording state
        self.recording = False
        self.camera_in_use = False
        self.frame_count = 0
        self.db = DataBase(resource_path('data/data.sqlite'), resource_path('data/last.json'))
        self.fr = FaceRecognizer(camera = 0, db = self.db)

    def _init_ui(self, title: str) -> None:
        """Initialize main window properties"""
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 800)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet(main_gui_style)

        app_font = QFont()
        app_font.setFamily("Arial")
        app_font.setPointSize(12)
        self.setFont(app_font)


    def _create_media_components(self) -> None:
        """Create video display components"""
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.video_label.setMinimumSize(640, 480)
        
        # Set default camera logo
        self.camera_logo = QPixmap("data/assets/camera_logo.png")
        self.video_label.setPixmap(self.camera_logo)

    def _create_info_panel(self) -> None:
        """Create right-side information panel"""
        self.info_panel = QFrame()
        self.info_panel.setFrameShape(QFrame.StyledPanel)
        info_layout = QVBoxLayout(self.info_panel)
        
        # Panel title
        title_label = QLabel("Yo`qlamachi yuzni tanish ilovasi")
        title_label.setStyleSheet("font-size: 20px; ")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Status indicators
        self.status_label = QLabel("Status: <span style='color: #00FF00;'> tayyor </span>")
        self.confidence_label = QLabel("Aniqlik: --%")
        self.user_label = QLabel("Foydalanuvchi: --")
        self.id_label = QLabel("ID: --")
        
        # Style information labels
        for label in [self.status_label, self.confidence_label, self.user_label, self.id_label]:
            label.setAlignment(Qt.AlignCenter)
            if label == self.status_label:
                label.setStyleSheet("font-size: 18px; color: #00FF00;")
            else:
                label.setStyleSheet("font-size: 16px;")

        self.sytem_status_ = QLabel("Sistema statusi: <span style='color: #00FF00;'>online</span>")
        self.sytem_status_.setStyleSheet("font-size: 16px; color: white;")
        self.sytem_status_.setTextFormat(Qt.RichText)

        # Face preview image
        self.image_label = QLabel()
        info_image = QPixmap(Params.face_logo)
        self.image_label.setPixmap(info_image.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setAlignment(Qt.AlignCenter)

        # Assemble info panel
        info_layout.addWidget(title_label)
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.image_label)
        info_layout.addWidget(self.user_label)
        info_layout.addWidget(self.confidence_label)
        info_layout.addWidget(self.id_label)
        info_layout.addStretch()
        info_layout.addWidget(self.sytem_status_)

    def _create_control_buttons(self) -> None:
        """Create and style control buttons"""
        self.start_button = QPushButton("▶️ Ishga tushrish")
        self.stop_button = QPushButton("⏹️ To'xtatish")
        self.exit_button = QPushButton("⏏️ Chiqish")
        
        # Button styling
        self.start_button.setStyleSheet("background-color: #006400; color: #00FF00;")
        self.stop_button.setStyleSheet("background-color: #640000; color: #FF0000;")
        self.exit_button.setStyleSheet("background-color: #4A4A4A; color: #FF0000;")

    def _setup_layouts(self) -> None:
        """Arrange UI components in layouts"""
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()

        # Left panel (video + buttons)
        left_panel.addWidget(self.video_label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.exit_button)
        left_panel.addLayout(button_layout)

        # Right panel (information)
        right_panel.addWidget(self.info_panel)

        # Combine layouts
        main_layout.addLayout(left_panel, 70)
        main_layout.addLayout(right_panel, 30)
        self.setLayout(main_layout)

    def _init_video(self) -> None:
        """Initialize video capture components"""
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def _connect_signals(self) -> None:
        """Connect UI signals to slots"""
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.exit_button.clicked.connect(self.close_app)

  

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.stop_recording()
            self.status_label.setText(f"Status: <span style='color: red;'>Kamera band</span>")
            QApplication.processEvents()
            return
        
        if ret:
            faces = self.fr.extract_faces(frame)
            if faces:
                face = faces[0]
                if face.size_to_large(frame):
                    self.show_frame(frame)
                
                elif face.size_to_small(frame):
                    cv2.rectangle(frame, (face.x, face.y), (face.x2, face.y2), Colors.RED, 2)
                    cv2.putText(frame, "Yaqinroq keling", (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.RED, 2)
                    self.show_frame(frame)
                
                elif face.moved_too_much():
                    Params.initial_face_position = None
                
                elif Params.countdown <= 0:
                    detect_frame = frame.copy()  # Create a copy to avoid modifying the original
                    cv2.rectangle(detect_frame, (face.x, face.y), (face.x2, face.y2), Colors.BLUE, 2)
                    cv2.putText(detect_frame, 'Aniqlanmoqda', (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.BLUE, 2)
                    self.show_frame(detect_frame)
                
                    QApplication.processEvents() 
                    camera()

                    Params.initial_face_position = None
                    ret, new_frame = self.cap.read()
                    if not ret:
                        return

                    users : list[User] = self.fr.find_face(frame, face)
                    if users:
                        self.check_faces(frame = frame, face = face, new_frame = new_frame, users = users)
                    
                    else:
                        cv2.rectangle(frame, (face.x, face.y), (face.x2, face.y2), Colors.RED, 2)
                        # cv2.putText(frame, 'Ro`yxatdan o`tmagan', (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.RED, 2)
                        self.show_frame(frame)
                        QApplication.processEvents()
                        wrong()
                        if self.timer.isActive():
                            self.timer.stop()
                        QTimer.singleShot(5000, self.reset_info_panel)

                else:
                    start_time = Params.start_time if Params.start_time else datetime.now()
                    elapsed_time = datetime.now() - start_time
                    if elapsed_time >= timedelta(seconds=1):
                        Params.countdown -= 1
                        Params.start_time = datetime.now()

                    cv2.rectangle(frame, (face.x, face.y), (face.x2, face.y2), Colors.BLUE, 2)
                    cv2.putText(frame, f'Qimirlamay turing {Params.countdown}', (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.BLUE, 2)
                    self.show_frame(frame)
                    
            else:
                self.show_frame(frame)
                      
    

    def show_frame(self, frame : MatLike):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
        self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def check_faces(self, frame: MatLike = None, new_frame: MatLike = None, face: Face = None, users: list[User] = []) -> bool:
        found = False

        for user in users:
            res: VerifyResolt = self.fr.verify_face(frame, face, user)
            if res.verified:
                cv2.rectangle(new_frame, (face.x, face.y), (face.x2, face.y2), Colors.GREEN, 2)
                # cv2.putText(new_frame, f'{user.name} {res.similarity_score}', (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.GREEN, 2)
            
                found = True

                # Show user image immediately
                info_image = QPixmap(user.photo_path)
                self.image_label.setPixmap(info_image.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.user_label.setText(f"Foydalanuvchi: <span style='color: #00FF00;font-size: 16px;'>{user.name}</span>")
                self.confidence_label.setText(f"Aniqlik: <span style='color: #00FF00;font-size: 16px;'>{res.similarity_score}</span>")
                self.id_label.setText(f"ID: <span style='color: #00FF00;font-size: 16px;'>{user.id}</span>")

                self.confidence_label
                self.show_frame(new_frame)
                
                group = self.db.get_group(user.group)
                if group:
                    if group.is_marked(user):
                        self.status_label.setText(f"Status: Allaqachon yo'qlama qilngan")
                        self.status_label.setStyleSheet("font-size: 18px; color: #FFFF00;")
                    else:
                        self.status_label.setText(f"Status: Yo'qlama qilndi")
                        self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")
                
                QApplication.processEvents()
                correct()

                if self.timer.isActive():
                    self.timer.stop()
                QTimer.singleShot(5000, self.reset_info_panel)
                break

        if not found:
            cv2.rectangle(new_frame, (face.x, face.y), (face.x2, face.y2), Colors.RED, 2)
            cv2.putText(new_frame, 'Ro`yxatdan o`tmagan', (face.x, face.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Colors.RED, 2)
            self.user_label.setText(f"Foydalanuvchi: <span style='color: red;font-size: 16px;'>Nomalum</span>")
    
            self.show_frame(new_frame)
            wrong()


            if self.timer.isActive():
                self.timer.stop()
            QTimer.singleShot(5000, self.reset_info_panel)
            

        return found
    
    def reset_info_panel(self):
        """Reset info panel to default state"""
        info_image = QPixmap(resource_path("data/assets/face.png"))
        self.image_label.setPixmap(info_image.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.user_label.setText("Foydalanuvchi: --")
        # self.user_label.setStyleSheet("font-size: 16px; color: white;")
        self.confidence_label.setText("Aniqlik: --%")
        self.id_label.setText("ID: --")

        
        # Style information labels
        for label in [self.status_label, self.confidence_label, self.user_label, self.id_label]:
            label.setAlignment(Qt.AlignCenter)
            if label == self.status_label:
                self.status_label.setText(f"Status: Ishlamoqda")
                label.setStyleSheet("font-size: 18px; color: #00FF00;")
            else:
                label.setStyleSheet("font-size: 16px;")

        if not self.timer.isActive():
            self.timer.start(30)
    
    def start_recording(self):
        if not self.recording:
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            self.recording = True
            self.camera_in_use = False
            self.timer.start(30)
            self.start_button.setStyleSheet("background-color: #004400; color: #00FF00;")
            self.status_label.setText("Status: ishlamoqda ...")
            self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")
            self.id_label.setText(f"ID: --")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.timer.stop()
            self.start_button.setStyleSheet("background-color: #006400; color: #00FF00;")
            self.status_label.setText("Status: to`xtatildi")
            self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")
            self.id_label.setText(f"ID: --")

            self.camera_logo = QPixmap(resource_path("data/assets/camera_logo.png"))
            self.video_label.setPixmap(self.camera_logo)

            self.cap.release()

    def close_app(self):
        self.timer.stop()
        self.cap.release()
        self.close()
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceIdApp()
    window.showMaximized()
    sys.exit(app.exec_())