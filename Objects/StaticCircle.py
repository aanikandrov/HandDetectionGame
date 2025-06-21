from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush

from Objects.GameObject import GameObject

class StaticCircle(GameObject):
    def __init__(self, x, y, radius, color):
        super().__init__(x, y, color)
        self.radius = radius

    def get_center(self):
        return QPointF(self.x, self.y)

    def draw(self, painter):
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(self.get_center(), self.radius, self.radius)

