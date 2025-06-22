import os
import sys
import time

import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QMainWindow, QLabel, QSpinBox, QPushButton, QVBoxLayout)

from HandTrackerThread import HandTrackerThread
from HandCursorWidget import HandCursorWidget
from Processing.ProcessingWindow import ProcessingWindow
from RulesDialog import RulesDialog


class MainWindow(QMainWindow):
    """ Инициализация главного окна, создание интерфейса и подключение сигналов """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 600)

        self.setStyleSheet("""
                    QMainWindow {
                        background-color: #1a1a8f;  /* Темно-синий фон */
                    }
                    QWidget {
                        background-color: #1a1a8f;
                        color: #ffffff;  /* Белый текст */
                        font-family: 'Courier New';
                        font-size: 12pt;
                    }
                    QPushButton {
                        background-color: #ff8800;  /* Оранжевый */
                        color: #000000;  /* Черный текст */
                        font-weight: bold;
                        border: 3px solid #ffffff;  /* Белая рамка */
                        padding: 5px;
                        min-height: 30px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #ffaa44;  /* Светло-оранжевый */
                        border: 3px solid #ffcc00;
                    }
                    QLabel {
                        color: #ffffff;
                        font-weight: bold;
                    }
                    QLabel#TimerLabel, QLabel#BestTimeLabel {
                        background-color: #000033;  /* Темно-синий фон */
                        border: 2px solid #ff8800;  /* Оранжевая рамка */
                        padding: 5px;
                        font-size: 16pt;
                    }
                    QSpinBox {
                        background-color: #000033;
                        color: #ffffff;
                        border: 2px solid #ff8800;
                        padding: 5px;
                        font-weight: bold;
                    }
                    QScrollArea {
                        background-color: #000033;
                        border: 3px solid #ff8800;
                    }
                """)

        pixel_font = QFont('Courier New', 10, QFont.Bold)
        self.setFont(pixel_font)

        # Переменные и флаги
        self.best_time = 0
        self.active_seconds = 0
        self.game_start_time = 0
        self.current_gesture = 0
        self.hand_detected = False
        self.game_paused = True
        self.processing_window_open = False

        # Центральный виджет
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный горизонтальный layout (игра слева, панель справа)
        main_horizontal_layout = QHBoxLayout(central_widget)
        main_horizontal_layout.setContentsMargins(10, 10, 10, 10)
        main_horizontal_layout.setSpacing(20)

        # Виджет игрового поля (слева)
        self.cursor_widget = HandCursorWidget()
        self.cursor_widget.setFixedSize(800, 800)
        main_horizontal_layout.addWidget(self.cursor_widget)

        # Вертикальный контейнер для правой панели
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Контейнер для системных кнопок
        system_container = QWidget()
        system_layout = QHBoxLayout(system_container)
        system_layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка правил
        self.rules_button = QPushButton("Правила")
        self.rules_button.setFixedSize(40, 40)
        self.rules_button.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.rules_button.setToolTip("Показать правила игры")
        self.rules_button.clicked.connect(self.show_rules)
        system_layout.addWidget(self.rules_button)

        # Кнопка закрытия
        self.close_button = QPushButton("Х")
        self.close_button.setFixedSize(40, 40)
        self.close_button.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.close_button.clicked.connect(self.close)
        system_layout.addWidget(self.close_button)

        right_layout.addWidget(system_container)

        # Контейнер для кнопок управления (Start, Restart)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка старт/пауза
        self.start_pause_button = QPushButton("Старт")
        self.start_pause_button.setFixedHeight(40)
        self.start_pause_button.clicked.connect(self.toggle_pause)
        self.start_pause_button.setEnabled(False)
        self.start_pause_button.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.start_pause_button.setToolTip("Поставить на паузу/продолжить")
        button_layout.addWidget(self.start_pause_button)

        # Кнопка перезапуска игры
        self.restart_button = QPushButton("Заново")
        self.restart_button.setFixedHeight(40)
        self.restart_button.clicked.connect(self.restart_game)
        self.restart_button.setEnabled(False)
        self.restart_button.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.restart_button.setToolTip("Начать игру заново")
        button_layout.addWidget(self.restart_button)

        right_layout.addWidget(button_container)

        # Контейнер для таймера и скорости
        timer_speed_container = QWidget()
        timer_speed_layout = QHBoxLayout(timer_speed_container)
        timer_speed_layout.setContentsMargins(0, 0, 0, 0)

        # Таймер
        timer_container = QWidget()
        timer_v_layout = QVBoxLayout(timer_container)
        timer_label = QLabel("Текущее время:")
        timer_label.setStyleSheet("font-weight: bold; font-size: 24px; color: #ff8800;")
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("TimerLabel")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFixedHeight(40)
        timer_v_layout.addWidget(timer_label)
        timer_v_layout.addWidget(self.timer_label)
        timer_speed_layout.addWidget(timer_container)

        # Элементы управления скоростью
        speed_container = QWidget()
        speed_v_layout = QVBoxLayout(speed_container)
        speed_label = QLabel("Скорость:")
        speed_label.setStyleSheet("font-weight: bold; font-size: 24px; color: #ff8800;")
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 15)
        self.speed_spinbox.setValue(1)
        self.speed_spinbox.valueChanged.connect(self.update_beetle_speed)
        self.speed_spinbox.setDisabled(True)
        self.speed_spinbox.setFixedHeight(40)
        speed_v_layout.addWidget(speed_label)
        speed_v_layout.addWidget(self.speed_spinbox)
        timer_speed_layout.addWidget(speed_container)

        right_layout.addWidget(timer_speed_container)

        # Контейнер для лучшего времени и правил
        best_rules_container = QWidget()
        best_rules_layout = QHBoxLayout(best_rules_container)
        best_rules_layout.setContentsMargins(0, 0, 0, 0)

        # Лучшее время
        best_time_container = QWidget()
        best_time_v_layout = QVBoxLayout(best_time_container)
        best_time_label = QLabel("Лучшее время:")
        best_time_label.setStyleSheet("font-weight: bold; font-size: 24px; color: #ff8800;")
        self.best_time_label_value = QLabel("00:00")
        self.best_time_label_value.setObjectName("BestTimeLabel")
        self.best_time_label_value.setAlignment(Qt.AlignCenter)
        self.best_time_label_value.setFixedHeight(40)
        best_time_v_layout.addWidget(best_time_label)
        best_time_v_layout.addWidget(self.best_time_label_value)
        best_rules_layout.addWidget(best_time_container)

        # Кнопка обработки данных
        self.processing_button = QPushButton("Обработка данных")
        self.processing_button.setFixedHeight(40)
        self.processing_button.clicked.connect(self.open_processing_window)
        self.restart_button.setStyleSheet("font-size: 24px; font-weight: bold;")
        right_layout.addWidget(self.processing_button)

        # Виджет камеры
        self.camera_widget = QLabel()
        self.camera_widget.setStyleSheet("""
                    border: 3px solid #ff8800;
                    background-color: #000033;
                    color: white;
                    font-size: 24px;
                    qproperty-alignment: AlignCenter;
                """)
        self.camera_widget.setFixedSize(400, 400)
        right_layout.addWidget(self.camera_widget)

        # Добавляем правую колонку в основной layout
        main_horizontal_layout.addWidget(right_panel)

        # Добавляем содержимое в главный layout
        # main_vertical_layout.addLayout(content_layout)

        # Thread для отслеживания руки
        self.tracker_thread = HandTrackerThread()
        self.tracker_thread.position_updated.connect(self.update_cursor_position_from_tracker)
        self.tracker_thread.landmarks_detected.connect(self.cursor_widget.set_hand_detected)
        self.tracker_thread.landmarks_detected.connect(self.set_hand_detected)
        self.tracker_thread.tracker_ready.connect(self.enable_start_button)
        self.tracker_thread.tracker_ready.connect(self.enable_start_button)
        self.tracker_thread.frame_updated.connect(self.update_camera)
        self.tracker_thread.start()

        # Таймер игры
        self.active_timer = QTimer(self)
        self.active_timer.setInterval(1000)
        self.active_timer.timeout.connect(self.update_active_timer)

        # Сигналы виджета
        self.cursor_widget.restart_requested.connect(self.restart_game)
        self.cursor_widget.game_ended.connect(self.on_game_ended)

        # Таймер для увеличения скорости
        self.speed_increase_timer = QTimer(self)
        self.speed_increase_timer.setInterval(5000)  # 5 секунд
        self.speed_increase_timer.timeout.connect(self.increase_beetle_speed)

        # Загрузка лучшего времени из файла
        self.load_best_time()


    def set_hand_detected(self, detected):
        """ Обновление статуса обнаружения руки """
        self.hand_detected = detected

    def update_active_timer(self):
        """ Обновление таймера во время игры """
        if (not self.game_paused and
                self.current_gesture == 0 and
                self.hand_detected):
            self.active_seconds += 1
            minutes = self.active_seconds // 60
            seconds = self.active_seconds % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def stop_tracker(self):
        if hasattr(self, 'tracker_thread') and self.tracker_thread and self.tracker_thread.isRunning():
            print("Stopping tracker thread...")
            self.tracker_thread.stop()

        # Очищаем виджет камеры (один раз)
        self.camera_widget.clear()
        self.camera_widget.setText("Камера отключена")
        self.camera_widget.setStyleSheet("""
                border: 2px solid #404040; 
                background-color: #333;
                color: white;
                font-size: 16pt;
                qproperty-alignment: AlignCenter;
            """)

        # Сбор мусора
        import gc
        gc.collect()

    def restart_tracker(self):
        """Перезапуск потока трекера руки"""
        if not self.tracker_thread.isRunning():
            self.tracker_thread = HandTrackerThread()
            self.tracker_thread.position_updated.connect(self.update_cursor_position_from_tracker)
            self.tracker_thread.landmarks_detected.connect(self.cursor_widget.set_hand_detected)
            self.tracker_thread.landmarks_detected.connect(self.set_hand_detected)
            self.tracker_thread.tracker_ready.connect(self.enable_start_button)
            self.tracker_thread.frame_updated.connect(self.update_camera)
            self.tracker_thread.start()

    def open_processing_window(self):
        """Открытие окна обработки данных"""
        if self.processing_window_open:
            print("Processing window is already open")
            return

        try:
            self.processing_window_open = True
            print("Stopping tracker...")
            self.stop_tracker()

            print("Waiting for resources release...")
            QTimer.singleShot(7000, self._open_processing_window)
        except Exception as e:
            print(f"Error opening processing window: {e}")
            self.processing_window_open = False
            self.restart_tracker()

    def _open_processing_window(self):
        try:
            self.processing_window = ProcessingWindow(self)
            self.processing_window.finished.connect(self.on_processing_finished)
            self.processing_window.exec_()
        except Exception as e:
            print(f"Error showing processing window: {e}")
            self.processing_window_open = False
            self.restart_tracker()

    def on_processing_finished(self):
        """Обработчик закрытия окна обработки"""
        self.processing_window_open = False
        self.restart_tracker()

    def format_time(self, seconds):
        """ Форматирование времени в формате MM:SS """
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def load_best_time(self):
        """ Загрузка лучшего времени из файла """
        try:
            if os.path.exists("Files/best_score.txt"):
                with open("Files/best_score.txt", "r") as f:
                    content = f.read().strip()
                    if content.isdigit():
                        self.best_time = int(content)
                        self.best_time_label_value.setText(self.format_time(self.best_time))
        except Exception as e:
            print(f"Error loading best time: {e}")

    def save_best_time(self):
        """ Сохранение лучшего времени в файл """
        try:
            with open("Files/best_score.txt", "w") as f:
                f.write(str(self.best_time))
        except Exception as e:
            print(f"Error saving best time: {e}")

    def best_time_to_file(self):
        """ Обновление лучшего времени при завершении игры """
        if self.active_seconds > self.best_time:
            self.best_time = self.active_seconds
            self.save_best_time()
            self.best_time_label_value.setText(self.format_time(self.best_time))

    def show_rules(self):
        """ Отображение диалог с правилами игры """
        dialog = RulesDialog(self)
        dialog.exec_()

    def toggle_pause(self):
        """ Переключение состояния паузы игры """
        if self.game_paused:
            self.active_timer.start()
            self.game_paused = False
            self.start_pause_button.setText("Пауза")
            self.speed_increase_timer.start()
            self.cursor_widget.game_paused = False
        else:
            self.game_paused = True
            self.start_pause_button.setText("Старт")
            self.speed_increase_timer.stop()
            self.active_timer.stop()
            self.cursor_widget.game_paused = True

    def on_game_ended(self):
        """ Обработка завершения игры """
        self.active_timer.stop()
        self.speed_increase_timer.stop()
        self.game_paused = True
        self.start_pause_button.setText("Старт")
        self.best_time_to_file()

    def restart_game(self):
        """ Перезапуск игры со сбросом состояний """
        # Обновление лучшего времени
        if self.active_seconds > self.best_time:
            self.best_time = self.active_seconds
            self.best_time_label_value.setText(self.format_time(self.best_time))
            self.best_time_to_file()

        # Остановка таймеров
        self.speed_increase_timer.stop()
        self.active_timer.stop()

        # Сброс переменных и флагов
        self.game_paused = True
        self.active_seconds = 0
        self.game_start_time = 0
        self.timer_label.setText("00:00")
        self.start_pause_button.setText("Старт")

        # Сброс скорости врагов
        self.cursor_widget.beetle.speed = 1
        self.cursor_widget.beetle2.speed = 1
        self.speed_spinbox.setValue(1)

        # Сброс игрового поля
        self.cursor_widget.reset_game()


    def enable_start_button(self, model_loaded):
        """ Активация кнопок управления """
        self.start_pause_button.setEnabled(model_loaded)
        self.restart_button.setEnabled(model_loaded)

    def increase_beetle_speed(self):
        """ Увеличение скорости врагов каждые 5 секунд """
        # Увеличиваем скорость только при открытой руке
        if (not self.game_paused and
                self.current_gesture == 0 and
                self.hand_detected):
            current_speed = self.cursor_widget.beetle.speed
            if current_speed < 10:
                new_speed = current_speed + 1
                self.cursor_widget.beetle.speed = new_speed
                self.cursor_widget.beetle2.speed = new_speed
                self.speed_spinbox.setValue(new_speed)

    def update_beetle_speed(self, speed):
        """ Обновление скорости врагов """
        self.cursor_widget.beetle.speed = speed
        self.cursor_widget.beetle2.speed = speed

    def update_cursor_position_from_tracker(self, x, y, gesture):
        """ Обновление позиции курсора на основе данных трекера """
        self.current_gesture = gesture
        self.cursor_widget.update_cursor_position(x, y, gesture)

    def update_camera(self, image):
        """ Обновление изображения с камеры """
        pixmap = QPixmap.fromImage(image)
        self.camera_widget.setPixmap(pixmap.scaled(
            self.camera_widget.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def closeEvent(self, event):
        """ Обработчик закрытия окна """
        try:
            print("Closing application...")
            # Останавливаем трекер
            self.stop_tracker()

            # Даем время на освобождение ресурсов
            if hasattr(self, 'tracker_thread') and self.tracker_thread:
                if self.tracker_thread.isRunning():
                    print("Waiting for tracker thread to finish...")
                    self.tracker_thread.wait(1000)

                    # Принудительно завершаем поток, если он все еще работает
                    if self.tracker_thread.isRunning():
                        print("Forcing tracker thread termination")
                        self.tracker_thread.terminate()
                        self.tracker_thread.wait(1000)

            print("Close event accepted")
            event.accept()
        except Exception as e:
            print(f"Error during close: {e}")
            event.accept()

        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())