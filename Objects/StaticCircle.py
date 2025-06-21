from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QBrush, QPixmap, QColor, QPainter
import os

from Objects.GameObject import GameObject


class StaticCircle(GameObject):
    def __init__(self, x, y, radius, color):
        super().__init__(x, y, color)
        self.radius = radius

        # Получаем абсолютный путь к изображению
        current_dir = os.path.dirname(os.path.abspath(__file__))
        texture_path = os.path.join(current_dir, 'earth.png')

        # Загружаем текстуру с проверкой
        self.texture = QPixmap()
        if not self.texture.load(texture_path):
            print(f"Error loading texture: {texture_path}")
            # Создаем цветной круг если текстура не загрузилась
            self.texture = None
        else:
            # Масштабируем изображение под размер круга
            self.texture = self.texture.scaled(
                2 * radius,
                2 * radius,
                Qt.IgnoreAspectRatio,  # Заполняем полностью без сохранения пропорций
                Qt.SmoothTransformation
            )

    def draw(self, painter):
        if self.texture:
            # Рисуем изображение в прямоугольнике, ограничивающем круг
            painter.drawPixmap(
                int(self.x - self.radius),
                int(self.y - self.radius),
                self.texture
            )
        else:
            # Рисуем цветной круг если текстура не загрузилась
            painter.setBrush(QBrush(self.color))
            painter.drawEllipse(
                QPointF(self.x, self.y),
                self.radius,
                self.radius
            )