from PyQt5.QtCore import QPointF

class GameObject:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def get_center(self):
        return QPointF(self.x, self.y)

    def draw(self, painter):
        pass