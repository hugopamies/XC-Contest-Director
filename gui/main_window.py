from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from gui.team_table import TeamRankingsTab
from gui.round_input import RoundInput
from gui.edit_scores import EditScoresTab
from gui.stats_dashboard import StatsDashboard
from gui.round_details import RoundDetailsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XtraChallenge 2025 Contest Director")
        self.setMinimumSize(1000, 800)

        tabs = QTabWidget()
        tabs.addTab(TeamRankingsTab(), "Teams & Rankings")
        tabs.addTab(RoundDetailsTab(), "Round Details")
        tabs.addTab(RoundInput(), "Input Round Data")
        tabs.addTab(EditScoresTab(), "Edit/Delete Scores")
        tabs.addTab(StatsDashboard(), "📈 Statistics")



        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(tabs)
        container.setLayout(layout)

        self.setCentralWidget(container)
