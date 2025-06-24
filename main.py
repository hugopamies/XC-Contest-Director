# UAV Contest Director App - Main Script

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.style import get_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setStyleSheet(get_stylesheet())
    window.show()
    sys.exit(app.exec())
