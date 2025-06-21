from PyQt5.QtGui import QBrush

from Objects.DraggableObject import DraggableObject

class DraggableSquare(DraggableObject):
    def draw(self, painter):
        color = self.color.lighter(150)
        painter.setBrush(QBrush(color))
        painter.drawRect(int(self.x), int(self.y), self.size, self.size)
