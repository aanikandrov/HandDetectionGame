import cv2
import numpy as np
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QMainWindow, QLabel, QVBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QImage, QPixmap, QBrush


class HandTrackerThread(QThread):
    position_updated = pyqtSignal(float, float, int)  # x, y, gesture
    frame_updated = pyqtSignal(QImage)
    landmarks_detected = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.running = True
        self.model = None
        self.cap = None
        self.labels_dict = {0: 'palm', 1: 'fist'}
        self.last_gesture = 0  # 0: fist, 1: palm

    def init_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            return False
        return True

    def load_model(self):
        try:
            import pickle
            model_dict = pickle.load(open('./model.p', 'rb'))
            self.model = model_dict['model']
            print("Model loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def run(self):
        if not self.init_camera() or not self.load_model():
            self.running = False
            return

        mp_hands = __import__('mediapipe').solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=True,
            min_detection_confidence=0.5,
            max_num_hands=1,
            min_tracking_confidence=0.5
        )

        while self.running:
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            if not ret:
                continue

            H, W, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                self.landmarks_detected.emit(True)
                hand_landmarks = results.multi_hand_landmarks[0]

                # Calculate palm center (landmark 9)
                cx = int(hand_landmarks.landmark[9].x * W)
                cy = int(hand_landmarks.landmark[9].y * H)

                # Normalize position for cursor widget
                norm_x = cx / W
                norm_y = cy / H

                # Process landmarks for gesture recognition
                x_ = [lm.x for lm in hand_landmarks.landmark]
                y_ = [lm.y for lm in hand_landmarks.landmark]

                min_x, min_y = min(x_), min(y_)
                max_x, max_y = max(x_), max(y_)

                data_aux = []
                for lm in hand_landmarks.landmark:
                    if (max_x - min_x) > 0 and (max_y - min_y) > 0:
                        data_aux.append((lm.x - min_x) / (max_x - min_x))
                        data_aux.append((lm.y - min_y) / (max_y - min_y))
                    else:
                        data_aux.append(lm.x)
                        data_aux.append(lm.y)

                # Predict gesture
                try:
                    if len(data_aux) == 42:
                        prediction = self.model.predict([np.asarray(data_aux)])
                        gesture = int(prediction[0])
                        self.last_gesture = gesture
                except Exception as e:
                    print(f"Prediction error: {e}")
                    gesture = self.last_gesture

                # Emit position and gesture
                self.position_updated.emit(norm_x, norm_y, gesture)


                circle_color = (0, 0, 255) if gesture == 0 else (0, 255, 0)  # red/green
                cv2.circle(frame, (cx, cy), 10, circle_color, -1)
            else:
                self.landmarks_detected.emit(False)

            # Convert to QImage and emit
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
            self.frame_updated.emit(qt_image)

        # Cleanup
        if self.cap:
            self.cap.release()

    def stop(self):
        self.running = False
        self.wait()


class HandCursorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Cursor Controller")
        self.setStyleSheet("background-color: #f0f0f0; border: 2px solid #404040;")
        self.setMinimumSize(400, 400)
        self.cursor_pos = [0.5, 0.5]  # Normalized position (center)
        self.hand_detected = False
        self.gesture = 0  # 0: fist, 1: palm
        self.trail_positions = []
        self.trail_colors = []

    def update_cursor_position(self, x, y, gesture):
        self.cursor_pos = [x, y]
        self.gesture = gesture
        self.hand_detected = True

        # Save position for trail with color based on gesture
        color = QColor(255, 0, 0) if gesture == 0 else QColor(0, 255, 0)
        self.trail_positions.append((x * self.width(), y * self.height()))
        self.trail_colors.append(color)

        # Limit trail length
        if len(self.trail_positions) > 20:
            self.trail_positions.pop(0)
            self.trail_colors.pop(0)


        self.update()

    def set_hand_detected(self, detected):
        if not detected:
            self.hand_detected = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw border
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # Draw trail
        if len(self.trail_positions) > 1:
            for i in range(1, len(self.trail_positions)):
                pen = QPen(self.trail_colors[i], 2)
                painter.setPen(pen)

                x1 = int(self.trail_positions[i - 1][0])
                y1 = int(self.trail_positions[i - 1][1])
                x2 = int(self.trail_positions[i][0])
                y2 = int(self.trail_positions[i][1])
                painter.drawLine(x1, y1, x2, y2)

        # Draw cursor
        if self.hand_detected:
            color = QColor(255, 0, 0) if self.gesture == 0 else QColor(0, 200, 0)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            x = int(self.cursor_pos[0] * self.width())
            y = int(self.cursor_pos[1] * self.height())

            # Ensure cursor stays within bounds
            x = max(15, min(self.width() - 15, x))
            y = max(15, min(self.height() - 15, y))

            painter.drawEllipse(QPoint(x, y), 15, 15)

            # Draw center dot
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPoint(x, y), 5, 5)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Tracking System")
        self.setGeometry(100, 100, 1200, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # Create cursor widget
        self.cursor_widget = HandCursorWidget()
        self.cursor_widget.setMinimumSize(500, 500)
        main_layout.addWidget(self.cursor_widget, 1)

        # Create camera widget
        self.camera_widget = QLabel()
        self.camera_widget.setAlignment(Qt.AlignCenter)
        self.camera_widget.setStyleSheet("border: 2px solid #404040; background-color: #333;")
        self.camera_widget.setMinimumSize(500, 500)
        main_layout.addWidget(self.camera_widget, 1)

        # Create tracker thread
        self.tracker_thread = HandTrackerThread()
        self.tracker_thread.position_updated.connect(self.cursor_widget.update_cursor_position)
        self.tracker_thread.landmarks_detected.connect(self.cursor_widget.set_hand_detected)
        self.tracker_thread.frame_updated.connect(self.update_camera)
        self.tracker_thread.start()

        # Status bar
        self.statusBar().showMessage("Tracking ready. Show your hand to the camera.")

    def update_camera(self, image):
        pixmap = QPixmap.fromImage(image)
        self.camera_widget.setPixmap(pixmap.scaled(
            self.camera_widget.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def closeEvent(self, event):
        self.tracker_thread.stop()
        self.tracker_thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())