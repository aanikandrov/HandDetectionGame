from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import (QWidget)


class HandCursorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Cursor Controller")
        self.setStyleSheet("background-color: #f0f0f0; border: 2px solid #404040;")
        self.setMinimumSize(400, 400)
        self.cursor_pos = [0.5, 0.5]
        self.hand_detected = False
        self.gesture = 0  # 0: fist, 1: palm

        self.trail_positions = []       # Позиции для следа
        self.trail_colors = []          # Цвет следа
        self.is_trail = True            # Флаг следа
        self.trail_max_length = 20      # Максимальная длина следа

        self.square_size = 100          # Размер квадрата
        self.square_x = 100             # Начальная позиция X
        self.square_y = 100             # Начальная позиция Y
        self.dragging = False           # Флаг перетаскивания
        self.cursor_over_square = False # Курсор над квадратом

    def update_cursor_position(self, x, y, gesture):
        # Абсолютные координаты курсора
        abs_x = x * self.width()
        abs_y = y * self.height()

        # Проверка наведения на квадрат
        self.cursor_over_square = (
            int(self.square_x) <= abs_x <= int(self.square_x) + self.square_size and
            int(self.square_y) <= abs_y <= int(self.square_y) + self.square_size
        )

        # Логика перетаскивания
        if gesture == 1:  # Кулак (зажатие)
            if self.dragging:
                # Продолжаем перетаскивание
                self.square_x = abs_x - self.square_size // 2
                self.square_y = abs_y - self.square_size // 2
            elif self.cursor_over_square:
                # Начинаем перетаскивание только если курсор над квадратом
                self.dragging = True
                # Центрируем квадрат относительно курсора
                self.square_x = abs_x - self.square_size // 2
                self.square_y = abs_y - self.square_size // 2
        else:  # Ладонь (разжатие)
            self.dragging = False

        self.cursor_pos = [x, y]
        self.gesture = gesture
        self.hand_detected = True

        if self.is_trail:
            color = QColor(255, 0, 0) if gesture == 0 else QColor(0, 255, 0)
            self.trail_positions.append((x * self.width(), y * self.height()))
            self.trail_colors.append(color)

            if len(self.trail_positions) > self.trail_max_length:
                self.trail_positions.pop(0)
                self.trail_colors.pop(0)

        self.update()

    def set_hand_detected(self, detected):
        if not detected:
            self.hand_detected = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # Отрисовка следа
        if self.is_trail and len(self.trail_positions) > 1:
            for i in range(1, len(self.trail_positions)):
                pen = QPen(self.trail_colors[i], 2)
                painter.setPen(pen)

                x1 = int(self.trail_positions[i - 1][0])
                y1 = int(self.trail_positions[i - 1][1])
                x2 = int(self.trail_positions[i][0])
                y2 = int(self.trail_positions[i][1])
                painter.drawLine(x1, y1, x2, y2)

        # Draw square
        square_color = QColor(65, 105, 225)  # Синий
        if self.dragging:
            square_color = square_color.lighter(150)  # Подсветка при перетаскивании
        painter.setBrush(QBrush(square_color))
        painter.drawRect(
            int(self.square_x),
            int(self.square_y),
            self.square_size,
            self.square_size
        )

        # Draw cursor
        if self.hand_detected:
            color = QColor(255, 0, 0) if self.gesture == 0 else QColor(0, 200, 0)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            x = int(self.cursor_pos[0] * self.width())
            y = int(self.cursor_pos[1] * self.height())

            # Ensure cursor stays within bounds
            x = max(15, min(self.width() - 15, x))
            y = max(15, min(self.height() - 15, y))

            size = 20 if self.gesture == 0 else 10
            painter.drawEllipse(QPoint(x, y), size, size)

            # Draw center dot
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPoint(x, y), 5, 5)
