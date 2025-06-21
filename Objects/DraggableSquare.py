from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPixmap
import os

from Objects.DraggableObject import DraggableObject

class DraggableSquare(DraggableObject):
    """ Квадрат с текстурой """
    def __init__(self, x, y, size, color):
        super().__init__(x, y, size, color)

        # Текстура из файла
        texture_path = os.path.join('Images/block.png')
        self.texture = QPixmap()

        if not self.texture.load(texture_path):
            print(f"Error loading texture: {texture_path}")
            self.texture = None
        else:
            # Масштабируем текстуру под размер квадрата
            self.texture = self.texture.scaled(
                size, size,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

    def draw(self, painter):
        """ Отрисовка текстуры """
        if self.texture:
            # Рисуем текстуру
            painter.drawPixmap(
                int(self.x),
                int(self.y),
                self.texture
            )
        else:
            # Текстуры нет - тогда заливаем цветом
            color = self.color.lighter(150)
            painter.setBrush(QBrush(color))
            painter.drawRect(int(self.x), int(self.y), self.size, self.size)