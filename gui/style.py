def get_stylesheet():
    return """
    QWidget {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 12px;
        background-color: #f8f9fa;
        color: #333;
    }

    QMainWindow {
        background-color: #ffffff;
    }

    QTabWidget::pane {
        border: 1px solid #cccccc;
        border-radius: 6px;
        background-color: #e9ecef;
    }

    QTabBar::tab {
        background: #d6d6d6;
        border: 1px solid #cccccc;
        border-bottom: none;
        padding: 8px 14px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: 500;
    }

    QTabBar::tab:selected {
        background: #ffffff;
        font-weight: bold;
        color: #b50220;
    }

    QTabBar::tab:hover {
        background-color: #eeeeee;
    }

    QLabel {
        font-size: 13px;
    }

    QPushButton {
        background-color: #d6d6d6;
        border: 1px solid #ccc;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
    }

    QPushButton:hover {
        background-color: #bbbbbb;
    }

    QPushButton:pressed {
        background-color: #aaaaaa;
    }

    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 4px;
    }

    QTableWidget {
        border: 1px solid #ddd;
        gridline-color: #ccc;
        selection-background-color: #ffebee;
        selection-color: #000;
        alternate-background-color: #f5f5f5;
    }

    QHeaderView::section {
        background-color: #d6d6d6;
        font-weight: bold;
        font-size: 14px;
        padding: 6px;
        border: 1px solid #bbb;
    }

    QScrollBar:vertical, QScrollBar:horizontal {
        background: #eee;
        width: 12px;
        height: 12px;
        margin: 0px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background: #ccc;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:hover {
        background: #aaa;
    }

    QGroupBox {
        border: 1px solid #ccc;
        border-radius: 6px;
        margin-top: 10px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 3px;
        background-color: transparent;
        font-weight: bold;
    }

    QToolTip {
        background-color: #fefefe;
        color: #000;
        border: 1px solid #ccc;
        padding: 4px;
    }
    """
