import numpy as np
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QApplication)

from Objects.ObjectWithTarget import ObjectWithTarget
from Objects.DraggableObject import DraggableObject
from Objects.StaticCircle import StaticCircle
from Objects.DraggableSquare import DraggableSquare

class HandCursorWidget(QWidget):
    restart_requested = pyqtSignal()
    game_ended = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Cursor Controller")
        self.setStyleSheet("background-color: #f0f0f0; border: 2px solid #404040;")
        self.setFixedSize(500, 500)
        self.cursor_pos = [0.5, 0.5]
        self.hand_detected = False
        self.gesture = 0  # 0: palm, 1: fist

        self.trail_positions = []       # Позиции для следа
        self.trail_colors = []          # Цвет следа
        self.is_trail = True            # Флаг следа
        self.trail_max_length = 20      # Максимальная длина следа

        self.dragging_square = None
        self.end_game = False
        self.end_game_timer = None
        self.game_paused = True
        self.game_start_time = 0
        self.game_end = False

        self.initial_positions = {
            'blue_square': (10, 10),
            'pink_square': (300, 100),
            'beetle': (400, 400),
            'circle': (200, 200)
        }

        blue_pos = self.initial_positions['blue_square']
        pink_pos = self.initial_positions['pink_square']
        beetle_pos = self.initial_positions['beetle']
        circle_pos = self.initial_positions['circle']

        self.pink_square = DraggableSquare(pink_pos[0], pink_pos[1], 100, QColor(255, 105, 180))
        self.beetle = ObjectWithTarget(beetle_pos[0], beetle_pos[1], 40, QColor(0, 128, 0))
        self.orange_circle = StaticCircle(circle_pos[0], circle_pos[1], 50, QColor(255, 165, 0))

        self.squares = [
            DraggableSquare(blue_pos[0], blue_pos[1], 100, QColor(65, 105, 225)),
            self.pink_square,
            self.beetle
        ]

        self.beetle.set_target(self.orange_circle)
        self.game_timer = QTimer()
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

    def reset_game(self):
        # Сброс позиций объектов
        self.squares[0].x, self.squares[0].y = self.initial_positions['blue_square']
        self.squares[1].x, self.squares[1].y = self.initial_positions['pink_square']
        self.squares[2].x, self.squares[2].y = self.initial_positions['beetle']
        self.orange_circle.x, self.orange_circle.y = self.initial_positions['circle']

        # Сброс состояния игры
        self.end_game = False
        self.game_end = False
        self.dragging_square = None

        # Сброс следа курсора
        self.trail_positions = []
        self.trail_colors = []

        # Сброс позиции курсора
        self.cursor_pos = [0.5, 0.5]

        # Ставим игру на паузу после рестарта
        self.game_paused = True

        self.update()


    def update_cursor_position(self, x, y, gesture):
        # Всегда обновляем позицию курсора, даже на паузе
        self.cursor_pos = [x, y]
        self.gesture = gesture
        self.hand_detected = True

        # Добавляем точку в след (если включен)
        if self.is_trail:
            color = QColor(255, 0, 0) if gesture == 0 else QColor(0, 255, 0)
            self.trail_positions.append((x * self.width(), y * self.height()))
            self.trail_colors.append(color)

            if len(self.trail_positions) > self.trail_max_length:
                self.trail_positions.pop(0)
                self.trail_colors.pop(0)

        # Если игра на паузе или завершена - только обновляем курсор
        if self.end_game or self.game_paused:
            self.update()
            return

        if gesture == 1:  # Кулак
            if self.game_timer.isActive():
                self.game_timer.stop()
        else:
            if not self.game_timer.isActive() and not self.game_paused:
                self.game_timer.start(1000)  # 1 секунда

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

        if gesture != 1:  # Только когда не зажато
            self.beetle.move_towards_target()

        if not self.end_game and self.check_circle_collision(self.beetle, self.orange_circle):
            self.show_end_game()

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
        # Проверяем все пары объектов
        for i in range(len(self.squares)):
            for j in range(i + 1, len(self.squares)):
                obj1 = self.squares[i]
                obj2 = self.squares[j]

                # Проверяем столкновение только между квадратами
                if isinstance(obj1, ObjectWithTarget) and isinstance(obj2, ObjectWithTarget):
                    continue

                if self.check_collision(obj1, obj2):
                    self.push_objects_apart(obj1, obj2)

        # Проверяем столкновения квадратов с кругом
        for square in self.squares:
            if not isinstance(square, ObjectWithTarget):  # Не проверяем столкновение жука с кругом
                if self.check_square_circle_collision(square, self.orange_circle):
                    self.push_square_from_circle(square, self.orange_circle)

    def check_collision(self, square1, square2):
        # Проверяем пересечение по осям X и Y
        return (square1.x < square2.x + square2.size and
                square1.x + square1.size > square2.x and
                square1.y < square2.y + square2.size and
                square1.y + square1.size > square2.y)

    def check_square_circle_collision(self, square, circle):
        """Проверяет столкновение квадрата и круга"""
        # Находим ближайшую точку на квадрате к центру круга
        closest_x = max(square.x, min(circle.x, square.x + square.size))
        closest_y = max(square.y, min(circle.y, square.y + square.size))

        # Расстояние между ближайшей точкой и центром круга
        distance = ((circle.x - closest_x) ** 2 + (circle.y - closest_y) ** 2) ** 0.5

        return distance < circle.radius

    def push_square_from_circle(self, square, circle):
        """Отталкивает квадрат от круга"""
        if square.dragging:
            return  # Не отталкиваем перетаскиваемый квадрат

        # Вектор от центра круга к центру квадрата
        square_center = square.get_center()
        circle_center = circle.get_center()

        dx = square_center.x() - circle_center.x()
        dy = square_center.y() - circle_center.y()

        # Если центры совпадают, добавляем случайное смещение
        if abs(dx) < 1e-5 and abs(dy) < 1e-5:
            dx = (np.random.rand() - 0.5) * 10
            dy = (np.random.rand() - 0.5) * 10

        # Нормализуем вектор
        length = max(1e-5, (dx ** 2 + dy ** 2) ** 0.5)
        dx /= length
        dy /= length

        # Минимальное расстояние (радиус круга + половина диагонали квадрата)
        min_distance = circle.radius + (square.size * 0.7)

        # Текущее расстояние между центрами
        current_distance = ((square_center.x() - circle_center.x()) ** 2 +
                            (square_center.y() - circle_center.y()) ** 2) ** 0.5

        # Если объекты пересекаются, отталкиваем квадрат
        if current_distance < min_distance:
            # Сила отталкивания
            force = (min_distance - current_distance) * 0.7

            # Смещаем квадрат от круга
            square.x += dx * force
            square.y += dy * force

    def check_circle_collision(self, beetle, circle):
        # Проверяем столкновение по расстоянию между центрами
        beetle_center = beetle.get_center()
        circle_center = circle.get_center()

        dx = circle_center.x() - beetle_center.x()
        dy = circle_center.y() - beetle_center.y()
        distance = (dx ** 2 + dy ** 2) ** 0.5

        # Сумма радиусов (для жука берем половину размера как радиус)
        min_distance = beetle.size / 2 + circle.radius

        return distance < min_distance

    def show_end_game(self):
        self.game_end = True
        self.end_game = True
        self.game_paused = True
        self.game_ended.emit()

        self.update()

        if self.game_timer.isActive():
            self.game_timer.stop()

        if hasattr(self, 'end_game_timer') and self.end_game_timer:
            self.end_game_timer.stop()





        self.end_game_timer = QTimer(self)
        self.end_game_timer.setSingleShot(True)
        self.end_game_timer.timeout.connect(self.restart_requested.emit)
        self.end_game_timer.timeout.connect(self.reset_game)
        self.end_game_timer.start(3000)

    def close_application(self):
        self.end_game_timer.stop()

        main_window = self.window()
        if main_window:
            main_window.close()

        QApplication.quit()



    def push_objects_apart(self, square1, square2):
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

        # Отрисовка оранжевого круга
        self.orange_circle.draw(painter)

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

        if self.game_end:
            painter.setPen(QColor(255, 0, 0))
            painter.setFont(QFont('Arial', 48, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "GAME END")
