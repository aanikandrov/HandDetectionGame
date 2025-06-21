from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush


class StaticCircle:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def get_center(self):
        return QPointF(self.x, self.y)

    def get_radius(self):
        return self.radius

    def draw(self, painter):
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(QPointF(int(self.x), int(self.y)),
                            int(self.radius), int(self.radius))

