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
                circle_size = 20 if gesture == 0 else 10  # red/green
                cv2.circle(frame, (cx, cy), circle_size, circle_color, -1)
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
