from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QFont
from styles import main_gui_style
from mytypes import Params, Face, VerificationResolt
import cv2, sys



class FaceIdApp(QWidget):
    def __init__(self, title : str = "Yo`qlamachi"):
        super().__init__()

        # Setup UI
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet(main_gui_style)

        app_font = QFont()
        app_font.setFamily("Arial")
        app_font.setPointSize(12)
        self.setFont(app_font)

        # Video label (Left Side)
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.video_label.setMinimumSize(640, 480)

        self.camera_logo = QPixmap("data/assets/camera_logo.png")
        self.video_label.setPixmap(self.camera_logo)

        # Info Panel (Right Side)
        info_panel = QFrame()
        info_panel.setFrameShape(QFrame.StyledPanel)
        info_layout = QVBoxLayout(info_panel)
        
        # Information labels
        self.status_label = QLabel("Status: tayyor")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")

        image_label = QLabel()
        info_image = QPixmap("data/assets/face.png")  # Replace with your image path
        image_label.setPixmap(info_image.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)
                
        self.confidence_label = QLabel("Confidence: --%")
        self.user_label = QLabel("User: Unknown")
        self.fps_label = QLabel("FPS: --")
        
        for label in [self.confidence_label, self.user_label, self.fps_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px;")

        # Add info widgets
        title = QLabel("Yuzni tanish ilovasi")
        title.setStyleSheet("font-size: 20px; ")
        title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(title)
        
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        info_layout.addWidget(image_label)
        info_layout.addWidget(self.user_label)
        info_layout.addWidget(self.confidence_label)
        info_layout.addWidget(self.fps_label)
        info_layout.addStretch()
        info_layout.addWidget(QLabel("Sistema statusi: online"))
        info_panel.setLayout(info_layout)



        # Buttons
        self.start_button = QPushButton("▶️ Ishga tushrish")
        self.stop_button = QPushButton("⏹️ To'xtatish")
        self.exit_button = QPushButton("⏏️ Chiqish")
        
        # Button styling
        self.start_button.setStyleSheet("background-color: #006400; color: #00FF00;")
        self.stop_button.setStyleSheet("background-color: #640000; color: #FF0000;")
        self.exit_button.setStyleSheet("background-color: #4A4A4A; color: #FF0000;")

        # Layouts
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()

        # Left Panel (Video + Controls)
        left_panel.addWidget(self.video_label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.exit_button)
        left_panel.addLayout(button_layout)

        # Right Panel (Information)
        right_panel.addWidget(info_panel)

        main_layout.addLayout(left_panel, 70)  # 70% width
        main_layout.addLayout(right_panel, 30)  # 30% width
        self.setLayout(main_layout)

        # OpenCV Video Capture
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Video Recorder
        self.recording = False
        self.frame_count = 0

        # Connect Buttons
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.exit_button.clicked.connect(self.close_app)
    


    def update_frame(self):
        """ Capture video frame and display it """
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            # Calculate FPS every 30 frames
            if self.frame_count % 30 == 0:
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                self.fps_label.setText(f"FPS: {fps:.1f}")
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def start_recording(self):
        """ Start recording video """
        if not self.recording:
            self.recording = True
            self.timer.start(30)
            self.start_button.setStyleSheet("background-color: #004400; color: #00FF00;")
            self.status_label.setText("Status: ishlamoqda ...")
            self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")

    def stop_recording(self):
        """ Stop recording video """
        if self.recording:
            self.recording = False
            self.timer.stop()
            self.start_button.setStyleSheet("background-color: #006400; color: #00FF00;")
            self.status_label.setText("Status: to`xtatildi")
            self.status_label.setStyleSheet("font-size: 18px; color: #00FF00;")

    def close_app(self):
        """ Close the application properly """
        self.timer.stop()
        self.cap.release()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceIdApp()
    window.showMaximized()
    sys.exit(app.exec_())
