from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from gui.team_table import TeamRankingsTab
from gui.round_input import RoundInput
from gui.edit_scores import EditScoresTab
from gui.stats_dashboard import StatsDashboard
from gui.round_details import RoundDetailsTab
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XtraChallenge 2025 Contest Director")
        icon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
        self.setWindowIcon(QIcon(icon_path))
        #self.setMinimumSize(1900, 1080)
        #self.showMaximized()

        tabs = QTabWidget()
        tabs.addTab(TeamRankingsTab(), "Rankings")
        tabs.addTab(RoundDetailsTab(), "Round Details")
        tabs.addTab(RoundInput(), "Input Data")
        tabs.addTab(EditScoresTab(), "Edit Data")
        tabs.addTab(StatsDashboard(), "Statistics Dashboard")



        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(tabs)
        container.setLayout(layout)

        self.setCentralWidget(container)
