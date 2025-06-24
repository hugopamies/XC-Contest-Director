from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QFormLayout, QLineEdit, QMessageBox
from scoring.scoring_engine import compute_round_score
from utils.storage import add_round_score
from PyQt6.QtWidgets import QInputDialog
import json
from PyQt6.QtWidgets import QComboBox
from utils.storage import load_results
from scoring.scoring_engine import get_best_values_per_round
from scoring.scoring_engine import compute_round_score
from utils.storage import add_round_score


class RoundInput(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # --- Team Selector ---
        layout.addWidget(QLabel("Select Team"))
        self.team_dropdown = QComboBox()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            self.teams = json.load(f)
        for category in ["Academic", "Clubs"]:
            for team in self.teams[category]:
                display = f"{team['id']} - {team['name']} ({category})"
                self.team_dropdown.addItem(display, (team["id"], category))
        layout.addWidget(self.team_dropdown)

        # --- Round Inputs Section ---
        form_section = QGroupBox("Round Input Data")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self.inputs = {
            "Requested Payload": QLineEdit(),
            "Unloaded Payload": QLineEdit(),
            "Time Circuit": QLineEdit(),
            "Time Glide": QLineEdit(),
            "Altitude": QLineEdit(),
            "Loading Time": QLineEdit(),
            # Pilot as dropdown
            "Pilot": QComboBox(),
            # Legal Flight as dropdown
            "Legal Flight": QComboBox(),
            # Good Landing as dropdown
            "Good Landing": QComboBox(),
            # Replacement Parts as dropdown
            "Replacement Parts": QComboBox()
        }

        # Set up Replacement Parts dropdown options
        self.inputs["Replacement Parts"].addItem("No Replacements Used", 1)
        self.inputs["Replacement Parts"].addItem("Replacements Used", 0)

        # Set up Good Landing dropdown options
        self.inputs["Good Landing"].addItem("Good Landing", 1)
        self.inputs["Good Landing"].addItem("Crash Landing", 0)

        # Set up Legal Flight dropdown options
        self.inputs["Legal Flight"].addItem("Legal", 1)
        self.inputs["Legal Flight"].addItem("Not Legal", 0)

        self.inputs["Pilot"].addItem("Team Pilot", 1)
        self.inputs["Pilot"].addItem("External Pilot", 0)

        # Takeoff Distance as dropdown
        takeoff_distance_dropdown = QComboBox()
        takeoff_distance_dropdown.addItem("20 m", 20)
        takeoff_distance_dropdown.addItem("40 m", 40)
        takeoff_distance_dropdown.addItem("60 m", 60)
        self.inputs["Takeoff Distance"] = takeoff_distance_dropdown

        for label, widget in self.inputs.items():
            form_layout.addRow(label, widget)

        form_section.setLayout(form_layout)
        layout.addWidget(form_section)

        # --- Submit Button ---
        submit_btn = QPushButton("✅ Submit Round Score")
        submit_btn.clicked.connect(self.compute_score)
        layout.addWidget(submit_btn)

        self.setLayout(layout)


    def compute_score(self):
        try:
            values = {}
            for k, widget in self.inputs.items():
                if isinstance(widget, QLineEdit):
                    values[k] = float(widget.text())
                elif isinstance(widget, QComboBox):
                    values[k] = widget.currentData()

            # For now, ask for team ID and category via popup (later improve with dropdowns)
            team_id, category = self.team_dropdown.currentData()

            round_index, ok = QInputDialog.getInt(self, "Round Number", "Enter round number (starting from 0):", min=0)
            if not ok:
                return
            
            results = load_results()
            best_Cdes, best_Tcarga, best_Tcircuit, best_Tglide = get_best_values_per_round(results, category, round_index)

            score = compute_round_score(
            values, category,
            best_unloaded_payload=best_Cdes,
            best_loading_time=best_Tcarga,
            best_circuit_time=best_Tcircuit,
            best_glide_time=best_Tglide
            )

            add_round_score(team_id, category, {
                "score": score,
                "inputs": values,
                "round": round_index
            })


            QMessageBox.information(self, "Score", f"Score recorded: {score}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid input: {e}")

