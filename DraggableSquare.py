from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush

class DraggableSquare:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.dragging = False

    def contains_point(self, point_x, point_y):
        return (self.x <= point_x <= self.x + self.size and
                self.y <= point_y <= self.y + self.size)

    def get_center(self):
        return QPointF(self.x + self.size / 2, self.y + self.size / 2)

    def draw(self, painter):
        color = self.color.lighter(150) if self.dragging else self.color
        painter.setBrush(QBrush(color))
        painter.drawRect(int(self.x), int(self.y), self.size, self.size)