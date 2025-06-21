from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class RulesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Rules")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()

        with open('Files/rules.txt', 'r', encoding='utf-8') as file:
            rules_text = file.read()

        rules_label = QLabel(rules_text)
        rules_label.setWordWrap(True)
        layout.addWidget(rules_label)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)