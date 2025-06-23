from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                             QProgressBar, QHBoxLayout, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal

from Processing.ProcessingThread import ProcessingThread

class ProcessingWindow(QDialog):
    """Окно для обработки данных и обучения модели"""

    finished = pyqtSignal()  # Сигнал закрытия окна
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Обработка данных и обучение модели")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setFixedSize(600, 500)

        # Основной layout
        layout = QVBoxLayout()

        # Группа для отображения текущего шага
        self.step_group = QGroupBox("Текущий шаг")
        step_layout = QVBoxLayout()

        self.step_label = QLabel("")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        step_layout.addWidget(self.step_label)

        self.instruction_label = QLabel("")
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setStyleSheet("font-size: 12pt;")
        step_layout.addWidget(self.instruction_label)

        self.step_group.setLayout(step_layout)
        layout.addWidget(self.step_group)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.start_button = QPushButton("Начать")
        self.start_button.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Назад")
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_button)

        layout.addLayout(btn_layout)

        # Журнал выполнения
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

        # Состояние обработки
        self.current_step = 0
        self.processing_thread = None
        self.update_step_info()

    def update_step_info(self):
        """Обновление информации о текущем шаге"""
        steps = [
            ("Шаг 1. Сбор данных",
             "1. Убедитесь, что камера подключена\n"
             "2. Нажмите 'Начать' для старта сбора данных\n"
             "3. Для каждого жеста следуйте инструкциям на экране"),

            ("Шаг 2. Разметка данных",
             "Идет обработка изображений с помощью MediaPipe\n"
             "Это может занять некоторое время..."),

            ("Шаг 3. Обучение модели",
             "Идет обучение модели Random Forest\n"
             "Это может занять некоторое время..."),

            ("Завершено!",
             "Обработка данных успешно завершена!\n"
             "Модель сохранена в файл model.p")
        ]

        if self.current_step < len(steps):
            title, instruction = steps[self.current_step]
            self.step_label.setText(title)
            self.instruction_label.setText(instruction)
        else:
            self.step_label.setText("Завершено!")
            self.instruction_label.setText("Все шаги успешно выполнены")

    def start_processing(self):
        try:
            """Запуск процесса обработки данных"""
            self.start_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.log_text.clear()

            # Проверяем, не существует ли предыдущий поток
            if hasattr(self, 'processing_thread') and self.processing_thread:
                try:
                    if self.processing_thread.isRunning():
                        self.processing_thread.cancel()
                        self.processing_thread.wait(1000)
                except:
                    pass

            # Создаем и запускаем поток обработки
            self.processing_thread = ProcessingThread(self.current_step)
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.log_message.connect(self.log_message)
            self.processing_thread.step_completed.connect(self.step_completed)
            self.processing_thread.start()
        except Exception as e:
            error_msg = f"Ошибка в окне обработки: {str(e)}"
            self.log_message.emit(error_msg)

            if "access violation" in str(e).lower():
                self.log_message.emit("Ошибка с доступом к камере")

            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(True)

    def update_progress(self, value):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)

    def log_message(self, message):
        """Добавление сообщения в журнал"""
        self.log_text.append(message)

    def step_completed(self, success):
        """Обработка завершения шага"""
        if success:
            self.current_step += 1
            self.update_step_info()
            self.progress_bar.setValue(0)

            if self.current_step < 4:
                self.log_message(f"Шаг {self.current_step} успешно завершен!")
                self.start_button.setEnabled(True)
                self.cancel_button.setEnabled(True)
            else:
                self.log_message("Все шаги успешно выполнены!")
                self.start_button.setEnabled(False)
                self.cancel_button.setEnabled(True)
        else:
            self.log_message("Произошла ошибка! Обработка прервана.")
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(True)

    def reject(self):
        """Обработка закрытия окна"""
        super().reject()
        self.finished.emit()