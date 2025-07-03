# UAV Contest Director App - Main Script

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from gui.style import get_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistency across platforms
    app.setStyleSheet(get_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())