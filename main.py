import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QMainWindow, QLabel, QSpinBox, QPushButton, QVBoxLayout)
from HandTrackerThread import HandTrackerThread
from HandCursorWidget import HandCursorWidget



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandTracker")
        self.setGeometry(100, 100, 1200, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный вертикальный layout
        main_vertical_layout = QVBoxLayout(central_widget)
        main_vertical_layout.setContentsMargins(10, 10, 10, 10)

        # Панель управления (верхняя панель)
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)

        # Кнопка старт/пауза
        self.start_pause_button = QPushButton("Start")
        self.start_pause_button.setFixedSize(100, 30)
        self.start_pause_button.clicked.connect(self.toggle_pause)
        # Изначально кнопка недоступна
        self.start_pause_button.setEnabled(False)

        # Таймер для увеличения скорости
        self.speed_increase_timer = QTimer(self)
        self.speed_increase_timer.setInterval(5000)  # 5 секунд
        self.speed_increase_timer.timeout.connect(self.increase_beetle_speed)

        self.restart_button = QPushButton("Restart")
        self.restart_button.setFixedSize(100, 30)
        self.restart_button.clicked.connect(self.restart_game)
        control_layout.addWidget(self.restart_button)


        # Таймер
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont('Arial', 16))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.timer_label.setFixedSize(100, 30)

        # Элементы управления скоростью
        speed_label = QLabel("Beetle Speed:")
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 10)
        self.speed_spinbox.setValue(1)
        self.speed_spinbox.valueChanged.connect(self.update_beetle_speed)

        # Добавляем элементы на панель
        control_layout.addWidget(self.start_pause_button)
        control_layout.addWidget(self.timer_label)
        control_layout.addWidget(speed_label)
        control_layout.addWidget(self.speed_spinbox)
        control_layout.addStretch()

        # Добавляем панель управления в главный layout
        main_vertical_layout.addWidget(control_panel)

        # Горизонтальный layout для основного содержимого (виджеты игры и камеры)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # Виджет курсора (игровое поле)
        self.cursor_widget = HandCursorWidget()
        self.cursor_widget.setFixedSize(500, 500)
        content_layout.addWidget(self.cursor_widget)

        self.active_seconds = 0
        self.current_gesture = 1

        # Виджет камеры
        self.camera_widget = QLabel()
        self.camera_widget.setAlignment(Qt.AlignCenter)
        self.camera_widget.setStyleSheet("border: 2px solid #404040; background-color: #333;")
        self.camera_widget.setFixedSize(500, 500)
        content_layout.addWidget(self.camera_widget)

        # Добавляем содержимое в главный layout
        main_vertical_layout.addLayout(content_layout)

        self.cursor_widget.restart_requested.connect(self.restart_game)

        # Thread трекера
        self.tracker_thread = HandTrackerThread()
        self.tracker_thread.position_updated.connect(self.update_cursor_position_from_tracker)
        self.tracker_thread.landmarks_detected.connect(self.cursor_widget.set_hand_detected)
        self.tracker_thread.frame_updated.connect(self.update_camera)
        self.tracker_thread.start()
        # Подключаем новый сигнал
        self.tracker_thread.model_loaded.connect(self.enable_start_button)

        # Инициализация таймера игры
        self.game_paused = True
        self.game_start_time = 0
        self.active_timer = QTimer(self)
        self.active_timer.setInterval(1000)
        self.active_timer.timeout.connect(self.update_active_timer)

    def update_active_timer(self):
        if not self.game_paused and self.current_gesture == 0:
            self.active_seconds += 1
            minutes = self.active_seconds // 60
            seconds = self.active_seconds % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def toggle_pause(self):
        if self.game_paused:
            self.active_timer.start()
            self.game_paused = False
            self.start_pause_button.setText("Pause")
            self.speed_increase_timer.start()
            #self.game_start_time = 0
            #self.timer_label.setText("00:00")
            self.cursor_widget.game_paused = False  # Обновляем состояние в виджете
        else:
            self.game_paused = True
            self.start_pause_button.setText("Start")
            self.speed_increase_timer.stop()
            self.active_timer.stop()
            self.cursor_widget.game_paused = True  # Обновляем состояние в виджете

    def restart_game(self):
        # Сброс таймера
        self.active_seconds = 0
        self.game_start_time = 0
        self.timer_label.setText("00:00")

        # Сброс состояния
        self.game_paused = True
        self.start_pause_button.setText("Start")

        # Остановка таймеров
        self.speed_increase_timer.stop()

        # Сброс виджета игры
        self.cursor_widget.reset_game()

        # Сброс скорости жука
        self.cursor_widget.beetle.speed = 1
        self.speed_spinbox.setValue(1)

    def enable_start_button(self, model_loaded):
        self.start_pause_button.setEnabled(model_loaded)

    def increase_beetle_speed(self):
        # Увеличиваем скорость только при ладони (gesture == 0)
        if not self.game_paused and self.current_gesture == 0:
            current_speed = self.cursor_widget.beetle.speed
            if current_speed < 10:
                new_speed = current_speed + 1
                self.cursor_widget.beetle.speed = new_speed
                self.speed_spinbox.setValue(new_speed)

    def update_cursor_position_from_tracker(self, x, y, gesture):
        self.current_gesture = gesture
        self.cursor_widget.update_cursor_position(x, y, gesture)

    def update_beetle_speed(self, speed):
        self.cursor_widget.beetle.speed = speed

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