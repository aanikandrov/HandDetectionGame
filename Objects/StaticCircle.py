from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QBrush, QPixmap, QColor, QPainter
import os

from Objects.GameObject import GameObject

class StaticCircle(GameObject):
    """ Класс статичного круга (цели)"""

    def __init__(self, x, y, radius, color):
        super().__init__(x, y, color)
        self.radius = radius
        self.default_texture = 'Images/pix-earth.png'
        self.load_texture(self.default_texture)

    def load_texture(self, texture_path):
        """ Загрузка или смена текстуры """
        self.texture = QPixmap()
        if not self.texture.load(texture_path):
            print(f"Error loading texture: {texture_path}")
            self.texture = None
        else:
            self.texture = self.texture.scaled(
                2 * self.radius,
                2 * self.radius,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

    def set_explosion(self):
        """ Установка текстуры взрыва """
        self.load_texture('Images/pix-explosion.png')

    def reset_texture(self):
        """ Восстановление исходной текстуры """
        self.load_texture(self.default_texture)

    def draw(self, painter):
        """ Отрисовка фигуры """
        if self.texture:
            painter.drawPixmap(
                int(self.x - self.radius),
                int(self.y - self.radius),
                self.texture
            )
        else:
            painter.setBrush(QBrush(self.color))
            painter.drawEllipse(
                QPointF(self.x, self.y),
                self.radius,
                self.radius
            )