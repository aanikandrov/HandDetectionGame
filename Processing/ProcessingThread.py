from PyQt5.QtCore import QThread, pyqtSignal

from Processing.Processing import collect_data, create_dataset, train_model

class ProcessingThread(QThread):
    """ Поток для выполнения обработки данных """
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    step_completed = pyqtSignal(bool)

    def __init__(self, start_step=0):
        super().__init__()
        self.start_step = start_step
        self.cancel_requested = False

    def run(self):
        """Основной метод потока"""
        try:
            # Шаг 1: Сбор данных
            if self.start_step <= 0 and not self.cancel_requested:
                self.log_message.emit("Начало сбора данных...")
                self.progress_updated.emit(0)  # Начало шага - 0%

                collect_data()

                self.log_message.emit("Сбор данных завершен!")
                self.progress_updated.emit(25)  # После шага 1 - 25%
                self.step_completed.emit(True)

            # Шаг 2: Разметка данных
            if self.start_step <= 1 and not self.cancel_requested:
                self.log_message.emit("Начало разметки данных...")
                self.progress_updated.emit(25)  # Начало шага - 25%

                create_dataset()

                self.log_message.emit("Разметка данных завершена!")
                self.progress_updated.emit(50)  # После шага 2 - 50%
                self.step_completed.emit(True)

            # Шаг 3: Обучение модели
            if self.start_step <= 2 and not self.cancel_requested:
                self.log_message.emit("Начало обучения модели...")
                self.progress_updated.emit(50)  # Начало шага - 50%

                train_model()

                self.log_message.emit("Обучение модели завершено!")
                self.progress_updated.emit(75)  # После шага 3 - 75%
                self.step_completed.emit(True)

            # Все шаги выполнены
            if not self.cancel_requested:
                self.log_message.emit("Все этапы обработки успешно завершены!")
                self.progress_updated.emit(100)  # После всех шагов - 100%

        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            self.log_message.emit(error_msg)

            if "access violation" in str(e).lower() or "0xC0000005" in str(e):
                self.log_message.emit("Ошибка с доступом к камере!")
            self.step_completed.emit(False)

    def cancel(self):
        """Запрос отмены обработки"""
        self.cancel_requested = True