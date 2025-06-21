import os
import sys

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
        self.setWindowTitle("Hand Gesture Controlled Game")
        self.setGeometry(100, 100, 1200, 600)

        # Переменные и флаги
        self.best_time = 0
        self.active_seconds = 0
        self.game_start_time = 0
        self.current_gesture = 0
        self.hand_detected = False
        self.game_paused = True

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный вертикальный layout
        main_vertical_layout = QVBoxLayout(central_widget)
        main_vertical_layout.setContentsMargins(10, 10, 10, 10)

        # Панель управления (верхняя панель)
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.addStretch()

        # Кнопка старт/пауза
        self.start_pause_button = QPushButton("Start")
        self.start_pause_button.setFixedSize(100, 30)
        self.start_pause_button.clicked.connect(self.toggle_pause)
        self.start_pause_button.setEnabled(False)
        self.start_pause_button.setToolTip("Поставить на паузу/продолжить")
        control_layout.addWidget(self.start_pause_button)

        # Кнопка перезапуска игры
        self.restart_button = QPushButton("Restart")
        self.restart_button.setFixedSize(100, 30)
        self.restart_button.clicked.connect(self.restart_game)
        self.restart_button.setEnabled(False)
        self.restart_button.setToolTip("Начать игру заново")
        control_layout.addWidget(self.restart_button)

        # Таймер
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont('Arial', 16))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.timer_label.setFixedSize(100, 30)
        self.timer_label.setToolTip("Текущее время")
        control_layout.addWidget(self.timer_label)

        # Таймер для увеличения скорости
        self.speed_increase_timer = QTimer(self)
        self.speed_increase_timer.setInterval(5000)  # 5 секунд
        self.speed_increase_timer.timeout.connect(self.increase_beetle_speed)

        # Элементы управления скоростью
        speed_label = QLabel("Enemy Speed:")
        control_layout.addWidget(speed_label)
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 15)
        self.speed_spinbox.setValue(1)
        self.speed_spinbox.valueChanged.connect(self.update_beetle_speed)
        self.speed_spinbox.setDisabled(True)
        self.speed_spinbox.setToolTip("Скорость астероидов")
        control_layout.addWidget(self.speed_spinbox)

        # Вывод лучшего времени
        self.best_time_label_text = QLabel("Best:")
        self.best_time_label_text.setFont(QFont('Arial', 16))
        control_layout.addWidget(self.best_time_label_text)

        self.best_time_label_value = QLabel("00:00")
        self.best_time_label_value.setFont(QFont('Arial', 16))
        self.best_time_label_value.setStyleSheet("background-color: #e0e0ff; border: 1px solid gray;")
        self.best_time_label_value.setFixedSize(130, 40)
        self.best_time_label_value.setToolTip("Лучшее время")
        control_layout.addWidget(self.best_time_label_value)

        # Кнопка вывода правил
        self.rules_button = QPushButton("?")
        self.rules_button.setFixedSize(40, 40)
        self.rules_button.setToolTip("Показать правила игры")
        self.rules_button.clicked.connect(self.show_rules)
        control_layout.addWidget(self.rules_button)

        # Добавляем панель управления в главный layout
        main_vertical_layout.addWidget(control_panel)

        # Кнопка вызова окна обработки данных
        self.processing_button = QPushButton("Обработка данных")
        self.processing_button.setFixedSize(120, 30)
        self.processing_button.clicked.connect(self.open_processing_window)
        control_layout.addWidget(self.processing_button)

        # Горизонтальный layout для основного содержимого (виджеты игры и камеры)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # Виджет курсора (игровое поле)
        self.cursor_widget = HandCursorWidget()
        self.cursor_widget.setFixedSize(800, 800)
        content_layout.addWidget(self.cursor_widget)

        # Вертикальный контейнер для правой колонки (камера + текст)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_layout.addStretch(1)

        # Виджет камеры
        self.camera_widget = QLabel()
        self.camera_widget.setAlignment(Qt.AlignCenter)
        self.camera_widget.setStyleSheet("border: 2px solid #404040; background-color: #333;")
        self.camera_widget.setFixedSize(500, 500)
        right_layout.addWidget(self.camera_widget)

        # Добавляем правую колонку в основной layout
        content_layout.addWidget(right_column, alignment=Qt.AlignBottom)

        # Добавляем содержимое в главный layout
        main_vertical_layout.addLayout(content_layout)

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
        if self.tracker_thread.isRunning():
            self.tracker_thread.stop()
            # Убрали ожидание здесь, так как оно уже в stop()

            # Очищаем виджет камеры
            self.camera_widget.clear()
            self.camera_widget.setText("Камера используется в окне обработки")
            self.camera_widget.setStyleSheet("""
                    border: 2px solid #404040; 
                    background-color: #333;
                    color: white;
                    font-size: 16pt;
                    qproperty-alignment: AlignCenter;
                """)

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
        # Останавливаем трекер руки перед открытием окна
        self.stop_tracker()

        # Задержка для полного освобождения ресурсов
        QTimer.singleShot(1500, self._open_processing_window)

    def _open_processing_window(self):
        self.processing_window = ProcessingWindow(self)
        self.processing_window.finished.connect(self.restart_tracker)
        self.processing_window.exec_()



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
            self.start_pause_button.setText("Pause")
            self.speed_increase_timer.start()
            self.cursor_widget.game_paused = False
        else:
            self.game_paused = True
            self.start_pause_button.setText("Start")
            self.speed_increase_timer.stop()
            self.active_timer.stop()
            self.cursor_widget.game_paused = True

    def on_game_ended(self):
        """ Обработка завершения игры """
        self.active_timer.stop()
        self.speed_increase_timer.stop()
        self.game_paused = True
        self.start_pause_button.setText("Start")
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
        self.start_pause_button.setText("Start")

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
        self.tracker_thread.stop()
        self.tracker_thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())