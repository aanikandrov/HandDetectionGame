from PyQt5.QtCore import QPointF

from Objects.GameObject import GameObject

class DraggableObject(GameObject):
    """ Базовый класс для перетаскиваемых объектов"""

    def __init__(self, x, y, size, color):
        super().__init__(x, y, color)
        self.size = size
        self.dragging = False

    def contains_point(self, point_x, point_y):
        """ Проверка, содержит ли объект указанную точку """
        # True если точка внутри объекта
        return (self.x <= point_x <= self.x + self.size and
                self.y <= point_y <= self.y + self.size)

    def get_center(self):
        return QPointF(self.x + self.size / 2, self.y + self.size / 2)