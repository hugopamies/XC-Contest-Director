from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QFormLayout, QLineEdit, QMessageBox, QInputDialog, QComboBox
import json
from utils.storage import add_round_score, load_results
from scoring.scoring_engine import get_best_values_per_round

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
            "Pilot": QComboBox(),
            "Legal Flight": QComboBox(),
            "Good Landing": QComboBox(),
            "Replacement Parts": QComboBox()
        }

        self.inputs["Replacement Parts"].addItem("No Replacements Used", 1)
        self.inputs["Replacement Parts"].addItem("Replacements Used", 0)
        self.inputs["Good Landing"].addItem("Good Landing", 1)
        self.inputs["Good Landing"].addItem("Crash Landing", 0)
        self.inputs["Legal Flight"].addItem("Legal", 1)
        self.inputs["Legal Flight"].addItem("Not Legal", 0)
        self.inputs["Pilot"].addItem("Team Pilot", 1)
        self.inputs["Pilot"].addItem("External Pilot", 0)

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
        submit_btn = QPushButton("✅ Submit Round Data (No Scoring)")
        submit_btn.clicked.connect(self.save_input_only)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def save_input_only(self):
        try:
            values = {}
            for k, widget in self.inputs.items():
                if isinstance(widget, QLineEdit):
                    values[k] = float(widget.text())
                elif isinstance(widget, QComboBox):
                    values[k] = widget.currentData()

            team_id, category = self.team_dropdown.currentData()

            round_index, ok = QInputDialog.getInt(self, "Round Number", "Enter round number (starting from 0):", min=0)
            if not ok:
                return

            add_round_score(team_id, category, {
                "inputs": values,
                "round": round_index
            })

            QMessageBox.information(self, "Saved", "Round input data saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid input: {e}")
