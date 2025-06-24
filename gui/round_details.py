from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox
)
import json
from utils.storage import load_results
from scoring.scoring_engine import compute_round_score, get_best_values_per_round


class RoundDetailsTab(QWidget):
    def __init__(self):
        super().__init__()

        # Layout setup
        self.layout = QVBoxLayout(self)

        # Category dropdown
        self.category_dropdown = QComboBox()
        self.category_dropdown.addItems(["Academic", "Clubs"])
        self.category_dropdown.currentTextChanged.connect(self.refresh_data)

        self.layout.addWidget(QLabel("Category"))
        self.layout.addWidget(self.category_dropdown)

        # Tab container for round tables
        self.round_tabs = QTabWidget()
        self.layout.addWidget(self.round_tabs)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.layout.addWidget(self.refresh_button)

        self.setLayout(self.layout)

        # Initial data load
        self.teams = []
        self.results = {}
        self.refresh_data()

    def refresh_data(self):
        # Load teams
        category = self.category_dropdown.currentText().lower()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams_data = json.load(f)
            self.teams = teams_data.get(category, [])

        # Load results
        self.results = load_results()

        # Rebuild round tabs
        self.build_round_tabs(category)

    def build_round_tabs(self, category):
        self.round_tabs.clear()

        # Determine number of rounds
        max_rounds = 0
        for team in self.teams:
            tid = str(team["id"])
            team_rounds = self.results.get(category, {}).get(tid, [])
            max_rounds = max(max_rounds, len(team_rounds))

        # Create a tab per round
        for round_index in range(max_rounds):
            tab = QWidget()
            layout = QVBoxLayout(tab)
            table = QTableWidget()
            layout.addWidget(table)
            self.round_tabs.addTab(tab, f"Round {round_index + 1}")

            self.populate_table(table, category, round_index)

    def populate_table(self, table, category, round_index):
        headers = [
            "Team ID", "Team Name",
            "Payload", "Circuit", "Glide",
            "Loading", "Altitude", "Total"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.teams))

        # Load best values for the round
        best_Cdes, best_Tcarga, best_Tcircuit, best_Tglide = get_best_values_per_round(
            self.results, category, round_index
        )
        best_eff = best_Cdes / (best_Tcarga ** 0.5) if best_Tcarga > 0 else 1

        for row, team in enumerate(self.teams):
            tid = str(team["id"])
            name = team["name"]

            team_rounds = self.results.get(category, {}).get(tid, [])
            if round_index >= len(team_rounds):
                values = ["0.00"] * 6 + ["0.00"]  # all subscores + total
            else:
                entry = team_rounds[round_index]
                inputs = entry.get("inputs", {})

                # Subscore calculations (replicate scoring engine logic)
                Cdes = inputs.get("Unloaded Payload", 0)
                Csol = inputs.get("Requested Payload", 1)
                Tcircuit = inputs.get("Time Circuit", 1)
                Tglide = inputs.get("Time Glide", 0)
                A60s = inputs.get("Altitude", 0)
                Tcarga = inputs.get("Loading Time", 1)

                weights = {
                    "academic": {
                        "payload": 150,
                        "circuit": 150,
                        "glide": 100,
                        "altitude": 100,
                        "loading": 100
                    },
                    "clubs": {
                        "payload": 200,
                        "circuit": 200,
                        "glide": 150,
                        "altitude": 150,
                        "loading": 100
                    }
                }

                w = weights.get(category, weights["academic"])

                payload_score = (
                    w["payload"] * (Cdes / best_Cdes) * (Cdes / Csol)
                    if Csol > 0 and best_Cdes > 0 else 0
                )
                circuit_score = (
                    w["circuit"] * (best_Tcircuit / Tcircuit)
                    if Tcircuit > 0 and best_Tcircuit > 0 else 0
                )
                glide_score = (
                    w["glide"] * (Tglide / best_Tglide)
                    if best_Tglide > 0 else 0
                )
                loading_score = (
                    w["loading"] * ((Cdes / (Tcarga ** 0.5)) / best_eff)
                    if Tcarga > 0 and best_eff > 0 else 0
                )
                altitude_score = min(w["altitude"], max(0, A60s - 40))

                total = compute_round_score(
                    inputs, category,
                    best_unloaded_payload=best_Cdes,
                    best_loading_time=best_Tcarga,
                    best_circuit_time=best_Tcircuit,
                    best_glide_time=best_Tglide
                )

                values = [
                    f"{payload_score:.2f}",
                    f"{circuit_score:.2f}",
                    f"{glide_score:.2f}",
                    f"{loading_score:.2f}",
                    f"{altitude_score:.2f}",
                    f"{total:.2f}",
                ]

            # Fill table row
            table.setItem(row, 0, QTableWidgetItem(tid))
            table.setItem(row, 1, QTableWidgetItem(name))
            for col, val in enumerate(values, start=2):
                table.setItem(row, col, QTableWidgetItem(val))

        table.resizeColumnsToContents()
