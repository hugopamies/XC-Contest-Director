from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QSplitter, QSizePolicy, QTabBar
)
from PyQt6.QtCore import QTimer, Qt
from utils.storage import load_results
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class StatsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.results = load_results()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            self.teams = json.load(f)

        self.round_index = 0
        self.total_rounds = self.get_max_rounds()
        self.auto_rotate = True
        self.auto_rotate_limit = 1  # 1 = only 1st round, 2 = first 2 rounds, 3 = first 3 rounds

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        nav_layout = QHBoxLayout()
        self.round_tabs = QTabBar()
        self.round_tabs.setShape(QTabBar.Shape.RoundedNorth)
        for i in range(self.total_rounds):
            self.round_tabs.addTab(f"Round {i + 1}")
        self.round_tabs.currentChanged.connect(self.select_round)

        self.toggle_button = QPushButton("⏸️ Auto-Rotate")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.toggle_auto_rotate)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)

        # Add buttons for auto-rotate range
        self.btn_show_1 = QPushButton("Limit 1")
        self.btn_show_2 = QPushButton("Limit 2")
        self.btn_show_3 = QPushButton("Limit 3")
        self.btn_show_1.setCheckable(True)
        self.btn_show_2.setCheckable(True)
        self.btn_show_3.setCheckable(True)
        self.btn_show_1.setChecked(True)

        self.btn_show_1.clicked.connect(lambda: self.set_auto_rotate_limit(1))
        self.btn_show_2.clicked.connect(lambda: self.set_auto_rotate_limit(2))
        self.btn_show_3.clicked.connect(lambda: self.set_auto_rotate_limit(3))

        nav_layout.addWidget(QLabel("Select Round:"))
        nav_layout.addWidget(self.round_tabs)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_show_1)
        nav_layout.addWidget(self.btn_show_2)
        nav_layout.addWidget(self.btn_show_3)
        nav_layout.addWidget(self.toggle_button)
        nav_layout.addWidget(self.refresh_button)
        main_layout.addLayout(nav_layout)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.left_splitter.setChildrenCollapsible(False)

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setChildrenCollapsible(False)

        self.init_team_trends_chart()
        self.init_best_metrics_tables()
        self.init_glide_chart()
        self.init_circuit_chart()

        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([2, 1])
        self.left_splitter.setSizes([2, 1])
        self.right_splitter.setSizes([1, 1])

        main_layout.addWidget(self.main_splitter)
        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_round)
        self.timer.start(10000)

        self.refresh_all()

    def set_auto_rotate_limit(self, limit):
        self.auto_rotate_limit = limit
        self.btn_show_1.setChecked(limit == 1)
        self.btn_show_2.setChecked(limit == 2)
        self.btn_show_3.setChecked(limit == 3)
        # Reset to first round if current round is out of new limit
        if self.round_index >= self.auto_rotate_limit:
            self.round_index = 0
            self.round_tabs.setCurrentIndex(self.round_index)
            self.refresh_all()
        self.reset_timer()

    def refresh_data(self):
        self.results = load_results()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            self.teams = json.load(f)
        self.total_rounds = self.get_max_rounds()
        # Update round tabs in case number of rounds changed
        self.round_tabs.clear()
        for i in range(self.total_rounds):
            self.round_tabs.addTab(f"Round {i + 1}")
        if self.round_index >= self.total_rounds:
            self.round_index = self.total_rounds - 1
        self.round_tabs.setCurrentIndex(self.round_index)
        self.refresh_all()

    def get_max_rounds(self):
        return max(
            max(len(self.results.get(cat, {}).get(str(team["id"]), [])) for team in self.teams.get(cat, []))
            for cat in ["Academic", "Clubs"]
        ) or 1

    def reset_timer(self):
        self.timer.stop()
        if self.auto_rotate:
            QTimer.singleShot(20000, lambda: self.timer.start(10000))

    def toggle_auto_rotate(self):
        self.auto_rotate = not self.auto_rotate
        if self.auto_rotate:
            self.timer.start(10000)
            self.toggle_button.setText("⏸️ Auto-Rotate")
        else:
            self.timer.stop()
            self.toggle_button.setText("▶️ Auto-Rotate")

    def next_round(self):
        # Only auto-rotate within the selected limit
        if self.auto_rotate_limit > self.total_rounds:
            limit = self.total_rounds
        else:
            limit = self.auto_rotate_limit
        self.round_index = (self.round_index + 1) % limit
        self.round_tabs.setCurrentIndex(self.round_index)
        self.refresh_all()
        self.reset_timer()

    def select_round(self, index):
        self.round_index = index
        self.refresh_all()
        self.reset_timer()

    def refresh_all(self):
        self.update_team_trends_chart()
        self.update_best_metrics_tables()
        self.update_glide_chart()
        self.update_circuit_chart()

    def init_team_trends_chart(self):
        layout = QVBoxLayout()
        label = QLabel(" Team Performance Trends")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        self.figure_trends, self.ax_trends = plt.subplots()
        self.canvas_trends = FigureCanvas(self.figure_trends)
        self.canvas_trends.setMinimumHeight(600)  # Ensure at least 600px tall
        layout.addWidget(self.canvas_trends)

        container = QWidget()
        container.setLayout(layout)
        self.left_splitter.addWidget(container)

    def update_team_trends_chart(self):
        self.ax_trends.clear()
        for cat in ["Academic", "Clubs"]:
            for team in self.teams[cat]:
                tid = str(team["id"])
                name = team["name"]
                rounds = self.results.get(cat, {}).get(tid, [])
                x, y = [], []
                # Compute R0 as static_score - penalties
                static_score = team.get("static_score", 0)
                penalties = team.get("penalties", 0)
                r0_score = static_score - penalties
                x.append(0)
                y.append(r0_score if isinstance(r0_score, (int, float)) else 0)
                # Add other rounds
                for i, entry in enumerate(rounds):
                    score = entry.get("score") if isinstance(entry, dict) else entry
                    if isinstance(score, (int, float)):
                        x.append(i + 1)
                        y.append(score)
                if x:
                    self.ax_trends.plot(x, y)
                    self.ax_trends.text(x[-1], y[-1], name, fontsize=7)

        self.ax_trends.set_title("Scores per Round", fontsize=11)
        self.ax_trends.set_xlabel("Round", fontsize=10)
        self.ax_trends.set_ylabel("Score", fontsize=10)
        self.ax_trends.set_ylim(0, 1000)
        self.ax_trends.set_xlim(-0.5, self.total_rounds + 0.5)
        self.ax_trends.set_xticks([0] + list(range(1, self.total_rounds + 1)))
        self.ax_trends.set_xticklabels(["R0"] + [f"R{i}" for i in range(1, self.total_rounds + 1)])
        self.figure_trends.tight_layout()
        self.canvas_trends.draw()

    def init_best_metrics_tables(self):
        # Place the two tables side by side using QHBoxLayout
        layout = QHBoxLayout()

        self.table_academic = self.create_metrics_table(" Academic Top Performers")
        self.table_clubs = self.create_metrics_table(" Clubs Top Performers")

        layout.addWidget(self.table_academic["container"])
        layout.addWidget(self.table_clubs["container"])

        container = QWidget()
        container.setLayout(layout)
        self.left_splitter.addWidget(container)

    def create_metrics_table(self, title):
        label = QLabel(title)
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        table = QTableWidget()
        table.setStyleSheet("font-size: 11px;")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Rank", "Top Payloads", "Top Circuit Times", "Top Gliding Times", "Top Loading Times"])
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(table)
        container = QWidget()
        container.setLayout(layout)
        return {"container": container, "table": table}

    def update_best_metrics_tables(self):
        r = self.round_index
        limits = {"Academic": 10, "Clubs": 3}

        for cat, table in [("Academic", self.table_academic["table"]), ("Clubs", self.table_clubs["table"])]:
            stats = []
            for team in self.teams[cat]:
                tid = str(team["id"])
                name = team["name"]
                rounds = self.results.get(cat, {}).get(tid, [])
                if r >= len(rounds):
                    continue
                inputs = rounds[r].get("inputs", {})
                stats.append({
                    "name": name,
                    "payload": inputs.get("Unloaded Payload", 0),
                    "circuit": inputs.get("Time Circuit", float("inf")),
                    "glide": inputs.get("Time Glide", 0),
                    "loading": inputs.get("Loading Time", float("inf"))
                })

            def rank(metric, reverse=True):
                return sorted(stats, key=lambda x: x[metric], reverse=reverse)[:limits[cat]]

            payloads = rank("payload")
            circuits = rank("circuit", reverse=False)
            glides = rank("glide")
            loadings = rank("loading", reverse=False)

            def safe_text(lst, idx, key):
                return f"{lst[idx]['name']} ({lst[idx][key]:.2f})" if idx < len(lst) else ""

            row_count = limits[cat]
            table.setRowCount(row_count)
            for i in range(row_count):
                rank_labels = ["1st", "2nd", "3rd"] + [f"{n+1}th" for n in range(3, 10)]
                label = rank_labels[i] if i < len(rank_labels) else f"{i+1}th"
                table.setItem(i, 0, QTableWidgetItem(label))
                
                table.setItem(i, 1, QTableWidgetItem(safe_text(payloads, i, "payload")))
                table.setItem(i, 2, QTableWidgetItem(safe_text(circuits, i, "circuit")))
                table.setItem(i, 3, QTableWidgetItem(safe_text(glides, i, "glide")))
                table.setItem(i, 4, QTableWidgetItem(safe_text(loadings, i, "loading")))

    def init_glide_chart(self):
        layout = QVBoxLayout()
        label = QLabel(" Glide Time Distribution")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        self.fig_glide, self.ax_glide = plt.subplots()
        self.canvas_glide = FigureCanvas(self.fig_glide)
        layout.addWidget(self.canvas_glide)
        container = QWidget()
        container.setLayout(layout)
        self.right_splitter.addWidget(container)

    def update_glide_chart(self):
        self.ax_glide.clear()
        for cat, color in zip(["Academic", "Clubs"], ["#B50220", "#4B0017"]):
            names, values = [], []
            for team in self.teams[cat]:
                tid = str(team["id"])
                name = team["name"]
                rounds = self.results.get(cat, {}).get(tid, [])
                if self.round_index < len(rounds):
                    inputs = rounds[self.round_index].get("inputs", {})
                    names.append(name)
                    values.append(inputs.get("Time Glide", 0))
            self.ax_glide.bar(names, values, label=cat, alpha=0.7)
        self.ax_glide.set_title(f"Glide Time - Round {self.round_index + 1}", fontsize=11)
        self.ax_glide.set_ylabel("Seconds", fontsize=10)
        self.ax_glide.tick_params(axis='x', labelrotation=45, labelsize=7)
        self.ax_glide.legend()
        self.fig_glide.tight_layout()
        self.canvas_glide.draw()

    def init_circuit_chart(self):
        layout = QVBoxLayout()
        label = QLabel(" Circuit Speed Distribution")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        self.fig_circuit, self.ax_circuit = plt.subplots()
        self.canvas_circuit = FigureCanvas(self.fig_circuit)
        layout.addWidget(self.canvas_circuit)
        container = QWidget()
        container.setLayout(layout)
        self.right_splitter.addWidget(container)

    def update_circuit_chart(self):
        self.ax_circuit.clear()
        for cat, color in zip(["Academic", "Clubs"], ["#B50220", "#4B0017"]):
            names, speeds = [], []
            for team in self.teams[cat]:
                tid = str(team["id"])
                name = team["name"]
                rounds = self.results.get(cat, {}).get(tid, [])
                if self.round_index < len(rounds):
                    inputs = rounds[self.round_index].get("inputs", {})
                    time = inputs.get("Time Circuit", 0)
                    speed = 1000 * 3.6 / time if time > 0 else 0
                    names.append(name)
                    speeds.append(speed)
            self.ax_circuit.bar(names, speeds, label=cat, alpha=0.7)
        self.ax_circuit.set_title(f"Circuit Speed - Round {self.round_index + 1}", fontsize=11)
        self.ax_circuit.set_ylabel("km/h", fontsize=10)
        self.ax_circuit.tick_params(axis='x', labelrotation=45, labelsize=7)
        self.ax_circuit.legend()
        self.fig_circuit.tight_layout()
        self.canvas_circuit.draw()
