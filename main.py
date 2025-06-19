import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout,
                             QMainWindow, QLabel)
from HandTrackerThread import HandTrackerThread
from HandCursorWidget import HandCursorWidget

# TODO вынести модель внешне

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandTracker")
        self.setGeometry(100, 100, 1200, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        # main_layout.setSpacing(20)

        # Виджет курсора
        self.cursor_widget = HandCursorWidget()
        self.cursor_widget.setMinimumSize(500, 500)
        main_layout.addWidget(self.cursor_widget, 1)

        # Виджет камеры
        self.camera_widget = QLabel()
        self.camera_widget.setAlignment(Qt.AlignCenter)
        self.camera_widget.setStyleSheet("border: 2px solid #404040; background-color: #333;")
        self.camera_widget.setMinimumSize(500, 500)
        main_layout.addWidget(self.camera_widget, 1)

        # Thread трекера
        self.tracker_thread = HandTrackerThread()
        self.tracker_thread.position_updated.connect(self.cursor_widget.update_cursor_position)
        self.tracker_thread.landmarks_detected.connect(self.cursor_widget.set_hand_detected)
        self.tracker_thread.frame_updated.connect(self.update_camera)
        self.tracker_thread.start()

        # self.statusBar().showMessage("Tracking ready. Show your hand to the camera.")

    def update_camera(self, image):
        pixmap = QPixmap.fromImage(image)
        self.camera_widget.setPixmap(pixmap.scaled(
            self.camera_widget.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def closeEvent(self, event):
        self.tracker_thread.stop()
        self.tracker_thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())