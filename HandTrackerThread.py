import os

import cv2
import pickle
import numpy as np

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage


class HandTrackerThread(QThread):
    """ Поток для отслеживания положения руки и распознавания жестов  """

    # Сигналы для взаимодействия с основным потоком
    landmarks_detected = pyqtSignal(bool)  # Обнаружены ли характерные точки руки
    position_updated = pyqtSignal(float, float, int)  # x, y, gesture
    frame_updated = pyqtSignal(QImage) # Обновление изображения с камеры
    tracker_ready = pyqtSignal(bool) # Готовность трекера к работе

    def __init__(self):
        """ Инициализация трекера руки """
        super().__init__()

        self.running = True # Флаг работы потока
        self.model = None   # Модель классификации жестов
        self.cap = None     # Объект захвата видео
        self.labels_dict = {0: 'palm', 1: 'fist'} # Словарь жестов
        # (palm - ладонь, fist - кулак)
        self.last_gesture = 0  # Последний распознанный жест

    def init_camera(self):
        """ Инициализация камеры"""
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            return False

        return True

    def load_model(self):
        """ Загрузка модели классификации из файла"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'Model', 'model.p')

            model_dict = pickle.load(open(model_path, 'rb'))
            self.model = model_dict['model']
            print("Model loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False


    def run(self):
        """ Основной цикл распознавания жестов"""

        # Инициализация камеры и модели
        camera_ok = self.init_camera()
        model_ok = self.load_model()
        self.tracker_ready.emit(camera_ok and model_ok)

        # Выход при ошибке инициализации
        if not camera_ok or not model_ok:
            self.running = False
            return

        # Инициализация Hands из MediaPipe
        mp_hands = __import__('mediapipe').solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=False,       # True - изображения отдельно,
                                           # False - с учетом предыдущих кадров
            min_detection_confidence=0.5,  # Мин порог доверия обнаружения
            max_num_hands=1,               # Максимальное кол-во рук
            min_tracking_confidence=0.5    # Мин порог доверия отслеживания
        )

        self.pixel_size = 0 # 8 сильный эффект
                            # 0 нет эффекта
        # TODO вынести в настройки

        try:
            while self.running:
                ret, frame = self.cap.read()
                # Зеркальное отображение (0 - обычное)
                frame = cv2.flip(frame, 1)
                if not ret:
                    continue

                # Размеры кадра
                H, W, _ = frame.shape
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Применение пиксельного эффекта
                if self.pixel_size > 1:
                    small = cv2.resize(
                        frame,
                        (frame.shape[1] // self.pixel_size,
                         frame.shape[0] // self.pixel_size),
                        interpolation=cv2.INTER_NEAREST
                    )
                    pixel_frame = cv2.resize(
                        small,
                        (frame.shape[1], frame.shape[0]),
                        interpolation=cv2.INTER_NEAREST
                    )
                else:
                    pixel_frame = frame

                # Обнаружение руки
                results = self.hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    self.landmarks_detected.emit(True)
                    hand_landmarks = results.multi_hand_landmarks[0]

                    # Центр руки (основание среднего пальца)
                    cx = int(hand_landmarks.landmark[9].x * W)
                    cy = int(hand_landmarks.landmark[9].y * H)

                    # Нормализация позиции курсора
                    norm_x = cx / W
                    norm_y = cy / H

                    # Подготовка данных для классификации
                    x_ = [lm.x for lm in hand_landmarks.landmark]
                    y_ = [lm.y for lm in hand_landmarks.landmark]
                    min_x, min_y = min(x_), min(y_)
                    max_x, max_y = max(x_), max(y_)

                    # Нормализация координат точек рук
                    data_aux = []
                    for lm in hand_landmarks.landmark:
                        if (max_x - min_x) > 0 and (max_y - min_y) > 0:
                            data_aux.append((lm.x - min_x) / (max_x - min_x))
                            data_aux.append((lm.y - min_y) / (max_y - min_y))
                        else:
                            data_aux.append(lm.x)
                            data_aux.append(lm.y)

                    # Классификация жеста
                    try:
                        if len(data_aux) == 42: # 21 точки, 2 координаты
                            prediction = self.model.predict([np.asarray(data_aux)])
                            gesture = int(prediction[0])
                            self.last_gesture = gesture
                    except Exception as e:
                        print(f"Prediction error: {e}")
                        gesture = self.last_gesture # Последний корректный жест

                    # Отправка позиций и жеста
                    self.position_updated.emit(norm_x, norm_y, gesture)

                    # Отрисовка курсора
                    circle_color = (0, 0, 255) if gesture == 0 else (0, 255, 0)  # red/green
                    circle_size = 20 if gesture == 0 else 10  # red/green
                    cv2.circle(frame, (cx, cy), circle_size, circle_color, -1)
                else:
                    self.landmarks_detected.emit(False)

                # Конвертация и отправка кадра
                h, w, ch = pixel_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(
                    pixel_frame.data,
                    w,
                    h,
                    bytes_per_line,
                    QImage.Format_BGR888
                )
                self.frame_updated.emit(qt_image)

        finally:
            try:
                if self.cap and self.cap.isOpened():
                    self.cap.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")

            try:
                if hasattr(self, 'hands') and self.hands:
                    self.hands.close()
            except Exception as e:
                print(f"Error closing MediaPipe resources: {e}")

    def stop(self):
        """ Остановка потока трекера руки """
        self.running = False
        if self.isRunning():
            self.wait(1000)
