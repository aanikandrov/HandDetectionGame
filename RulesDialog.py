from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class RulesDialog(QDialog):
    """Диалоговое окно с правилами игры """

    def __init__(self, parent=None):
        """Инициализация окна правил """
        super().__init__(parent)
        self.setWindowTitle("Game Rules")
        self.setFixedSize(500, 400)

        # Основной layout
        layout = QVBoxLayout()

        # Загрузка текста правил из файла
        try:
            with open('Files/rules.txt', 'r', encoding='utf-8') as file:
                rules_text = file.read()
        except FileNotFoundError:
            rules_text = "Файл правил не найден."
        except Exception as e:
            rules_text = f"Ошибка загрузки правил: {str(e)}"

        # Создание лейбла с правилами
        rules_label = QLabel(rules_text)
        rules_label.setWordWrap(True)
        layout.addWidget(rules_label)

        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)  # Закрытие диалога
        layout.addWidget(close_button)

        self.setLayout(layout)