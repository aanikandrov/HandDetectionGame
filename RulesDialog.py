from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor


class RulesDialog(QDialog):
    """Диалоговое окно с правилами игры """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Установка ретро-стиля
        self.setStyleSheet("""
                    QDialog {
                        background-color: #1a1a8f;
                    }
                    QScrollArea {
                        background-color: #000033;
                        border: 3px solid #ff8800;
                    }
                    QLabel {
                        background-color: #000033;
                        color: #ffffff;
                        padding: 10px;
                    }
                    /* Стили для заголовков */
                    h2 {
                        color: #ff8800;  /* Оранжевый для заголовков */
                        font-size: 18pt;
                    }
                    b, strong {
                        color: #ff8800;  /* Оранжевый для жирного текста */
                    }
                    QPushButton {
                        background-color: #ff8800;
                        color: #000000;
                        font-weight: bold;
                        border: 3px solid #ffffff;
                        padding: 8px;
                        min-height: 30px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #ffaa44;
                        border: 3px solid #ffcc00;
                    }
                    QPushButton:pressed {
                        background-color: #cc6600;
                    }
                """)

        # Основной layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Загрузка текста правил из файла
        try:
            with open('Files/rules.txt', 'r', encoding='utf-8') as file:
                rules_text = file.read()
        except FileNotFoundError:
            rules_text = "Файл правил не найден."
        except Exception as e:
            rules_text = f"Ошибка загрузки правил: {str(e)}"

        # Добавляем ретро-стили к тексту
        styled_text = f"""
                <div style="
                    font-family: 'Courier New', monospace;
                    font-size: 12pt;
                    color: #ffffff;
                ">
                {rules_text}
                </div>
                """

        # Создание лейбла с правилами
        rules_label = QLabel(styled_text)
        rules_label.setWordWrap(True)
        rules_label.setAlignment(Qt.AlignTop)
        rules_label.setMinimumWidth(450)

        # Добавляем область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidget(rules_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll_area)

        # Кнопка закрытия
        close_button = QPushButton("CLOSE")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setFixedSize(140, 45)
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("font-family: 'Courier New'; "
                                   "font-size: 24px;")

        layout.addWidget(close_button)
        layout.setAlignment(close_button, Qt.AlignCenter)

        self.setLayout(layout)

        pixel_font = QFont("Courier New", 10, QFont.Bold)
        self.setFont(pixel_font)