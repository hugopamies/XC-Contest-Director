def get_stylesheet():
    return """
        QWidget {
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
            color: #333;
            background-color: #f9f9f9;
        }

        QTabWidget::pane {
            border: 1px solid #ccc;
            background-color: #ffffff;
        }

        QTabBar::tab {
            background: #e0e0e0;
            padding: 8px 20px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background: #A8323E; /* Muted Red */;
            color: white;
        }

        QPushButton {
            background-color: #A8323E; /* Muted Red */;
            color: white;
            padding: 8px 16px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            margin: 5px 0;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QLineEdit, QComboBox, QListWidget {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-bottom: 6px;
        }

        QLabel {
            font-weight: 600;
            margin-top: 10px;
        }

        QTableWidget {
            border: 1px solid #ccc;
            background-color: #fff;
        }

        QHeaderView::section {
            background-color: #ddd;
            font-weight: bold;
            padding: 5px;
            border: 1px solid #ccc;
        }

        QScrollBar:vertical {
            width: 10px;
            background: #f0f0f0;
        }

        QScrollBar::handle:vertical {
            background: #ccc;
            border-radius: 4px;
        }
    """
