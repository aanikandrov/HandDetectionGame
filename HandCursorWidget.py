import numpy as np
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import (QWidget)

from DraggableSquare import DraggableSquare


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

        self.squares = [
            DraggableSquare(100, 100, 100, QColor(65, 105, 225)),  # Синий
            DraggableSquare(300, 100, 100, QColor(255, 105, 180))  # Розовый
        ]

        self.dragging_square = None

    def update_cursor_position(self, x, y, gesture):
        # Абсолютные координаты курсора
        abs_x = x * self.width()
        abs_y = y * self.height()

        # Проверка столкновений и отталкивание квадратов
        self.resolve_collisions()

        # Перетаскивание
        if gesture == 1:  # Кулак (зажатие)
            if self.dragging_square is not None:
                # Продолжаем перетаскивание текущего квадрата
                self.dragging_square.x = abs_x - self.dragging_square.size // 2
                self.dragging_square.y = abs_y - self.dragging_square.size // 2

                # Гарантируем, что перетаскиваемый квадрат остается в пределах
                self.ensure_square_in_bounds(self.dragging_square)
            else:
                # Проверяем, находится ли курсор над каким-либо квадратом
                for square in self.squares:
                    if square.contains_point(abs_x, abs_y):
                        # Начинаем перетаскивание этого квадрата
                        self.dragging_square = square
                        self.dragging_square.dragging = True
                        # Центрируем квадрат относительно курсора
                        self.dragging_square.x = abs_x - self.dragging_square.size // 2
                        self.dragging_square.y = abs_y - self.dragging_square.size // 2
                        break
        else:  # Ладонь (разжатие)
            if self.dragging_square is not None:
                self.dragging_square.dragging = False
                self.dragging_square = None

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

        # Обрабатываем столкновения со стенами
        self.resolve_wall_collisions()

        self.update()

    def ensure_square_in_bounds(self, square):
        # Левая граница
        if square.x < 0:
            square.x = 0

        # Верхняя граница
        if square.y < 0:
            square.y = 0

        # Правая граница
        if square.x + square.size > self.width():
            square.x = self.width() - square.size

        # Нижняя граница
        if square.y + square.size > self.height():
            square.y = self.height() - square.size

    def resolve_wall_collisions(self):
        for square in self.squares:
            self.ensure_square_in_bounds(square)

    def resolve_collisions(self):
        # Проверяем все пары квадратов
        for i in range(len(self.squares)):
            for j in range(i + 1, len(self.squares)):
                square1 = self.squares[i]
                square2 = self.squares[j]

                if self.check_collision(square1, square2):
                    self.push_squares_apart(square1, square2)

    def check_collision(self, square1, square2):
        # Проверяем пересечение по осям X и Y
        return (square1.x < square2.x + square2.size and
                square1.x + square1.size > square2.x and
                square1.y < square2.y + square2.size and
                square1.y + square1.size > square2.y)

    def push_squares_apart(self, square1, square2):
        # Рассчитываем вектор между центрами
        center1 = square1.get_center()
        center2 = square2.get_center()

        dx = center2.x() - center1.x()
        dy = center2.y() - center1.y()

        # Если квадраты находятся точно друг на друге, добавляем случайное смещение
        if abs(dx) < 1e-5 and abs(dy) < 1e-5:
            dx = (np.random.rand() - 0.5) * 10
            dy = (np.random.rand() - 0.5) * 10

        # Нормализуем вектор
        length = max(1e-5, (dx ** 2 + dy ** 2) ** 0.5)
        dx /= length
        dy /= length

        # Минимальное расстояние между центрами (диагональ квадратов)
        min_distance = (square1.size + square2.size) * 0.7

        # Текущее расстояние
        current_distance = ((center2.x() - center1.x()) ** 2 +
                            (center2.y() - center1.y()) ** 2) ** 0.5

        # Если квадраты пересекаются, отталкиваем их
        if current_distance < min_distance:
            # Сила отталкивания
            force = (min_distance - current_distance) * 0.5

            # Смещаем квадраты в противоположных направлениях
            if not square1.dragging:
                square1.x -= dx * force
                square1.y -= dy * force

            if not square2.dragging:
                square2.x += dx * force
                square2.y += dy * force

    def set_hand_detected(self, detected):
        if not detected:
            self.hand_detected = False
            # Сбрасываем перетаскивание при потере руки
            if self.dragging_square is not None:
                self.dragging_square.dragging = False
                self.dragging_square = None

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

        # Отрисовка квадратов
        for square in self.squares:
            square.draw(painter)

        # Отрисовка курсора
        if self.hand_detected:
            color = QColor(255, 0, 0) if self.gesture == 0 else QColor(0, 200, 0)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            x = int(self.cursor_pos[0] * self.width())
            y = int(self.cursor_pos[1] * self.height())

            # Обеспечиваем нахождение курсора в пределах виджета
            x = max(15, min(self.width() - 15, x))
            y = max(15, min(self.height() - 15, y))

            size = 20 if self.gesture == 0 else 10
            painter.drawEllipse(QPoint(x, y), size, size)

            # Отрисовка центральной точки
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPoint(x, y), 5, 5)
