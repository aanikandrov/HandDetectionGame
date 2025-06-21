from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QPixmap, QPolygonF
import os

from Objects.DraggableObject import DraggableObject


class ObjectWithTarget(DraggableObject):
    def __init__(self, x, y, size, color):
        super().__init__(x, y, size, color)
        self.speed = 1
        self.target = None

        # Загрузка текстуры stone.png
        current_dir = os.path.dirname(os.path.abspath(__file__))
        texture_path = os.path.join(current_dir, 'stone.png')

        self.texture = QPixmap()
        if not self.texture.load(texture_path):
            print(f"Error loading texture: {texture_path}")
            self.texture = None
        else:
            # Масштабируем изображение под размер объекта
            self.texture = self.texture.scaled(
                size, size,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

    def set_target(self, target):
        self.target = target

    def move_towards_target(self):
        if self.target is None or self.dragging:
            return False

        object_center = self.get_center()
        target_center = self.target.get_center()
        dx = target_center.x() - object_center.x()
        dy = target_center.y() - object_center.y()
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance < 10:
            return False

        if distance > 0:
            dx /= distance
            dy /= distance

        self.x += dx * self.speed
        self.y += dy * self.speed
        return True

    def draw(self, painter):
        if self.texture:
            # Рисуем текстуру
            painter.drawPixmap(
                int(self.x),
                int(self.y),
                self.texture
            )
        else:
            # Резервный вариант: цветной треугольник
            color = self.color.lighter(150) if self.dragging else self.color
            painter.setBrush(QBrush(color))
            points = [
                QPointF(self.x + self.size / 2, self.y),
                QPointF(self.x, self.y + self.size),
                QPointF(self.x + self.size, self.y + self.size)
            ]
            painter.drawPolygon(QPolygonF(points))