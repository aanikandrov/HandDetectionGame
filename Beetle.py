from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush, QPolygonF

class Beetle:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.dragging = False
        self.speed = 1
        self.target = None

    def contains_point(self, point_x, point_y):
        return (self.x <= point_x <= self.x + self.size and
                self.y <= point_y <= self.y + self.size)

    def get_center(self):
        return QPointF(self.x + self.size / 2, self.y + self.size / 2)

    def set_target(self, target_square):
        self.target = target_square

    def move_towards_target(self):
        if self.target is None or self.dragging:
            return False

        # Центр жука
        beetle_center = self.get_center()

        # Центр цели
        target_center = self.target.get_center()

        # Вектор к цели
        dx = target_center.x() - beetle_center.x()
        dy = target_center.y() - beetle_center.y()

        # Расстояние до цели
        distance = (dx ** 2 + dy ** 2) ** 0.5

        # Если расстояние маленькое, не двигаемся
        if distance < 10:
            return False

        # Нормализуем вектор
        if distance > 0:
            dx /= distance
            dy /= distance

        # Двигаемся к цели
        self.x += dx * self.speed
        self.y += dy * self.speed

        return True

    def draw(self, painter):
        color = self.color.lighter(150) if self.dragging else self.color
        painter.setBrush(QBrush(color))

        # Рисуем треугольник
        triangle_size = self.size
        points = [
            QPointF(self.x + triangle_size / 2, self.y),  # Верхняя вершина
            QPointF(self.x, self.y + triangle_size),  # Нижняя левая
            QPointF(self.x + triangle_size, self.y + triangle_size)  # Нижняя правая
        ]
        painter.drawPolygon(QPolygonF(points))