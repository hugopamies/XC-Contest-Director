from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QFormLayout, QLineEdit, QMessageBox, QInputDialog, QComboBox
import json
from utils.storage import add_round_score, load_results
from scoring.scoring_engine import get_best_values_per_round
from PyQt6.QtCore import Qt

class RoundInput(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # --- Team Selector ---
        team_selector_layout = QVBoxLayout()
        team_selector_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        team_label = QLabel("Select Team")
        team_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        team_selector_layout.addWidget(team_label)
        self.team_dropdown = QComboBox()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            self.teams = json.load(f)
        for category in ["Academic", "Clubs"]:
            for team in self.teams[category]:
                display = f"{team['id']} - {team['name']} ({category})"
                self.team_dropdown.addItem(display, (team["id"], category))
        team_selector_layout.addWidget(self.team_dropdown)
        layout.addLayout(team_selector_layout)

        # --- Round Inputs Section ---
        form_section = QGroupBox("Round Input Data")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

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

        # Set fixed width for inputs and center them
        self.input_width = 300  # Will be updated in resizeEvent

        for label, widget in self.inputs.items():
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.setFixedWidth(self.input_width)
            row_layout = QVBoxLayout()
            row_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            row_layout.addWidget(widget)
            form_layout.addRow(label, widget)

        form_section.setLayout(form_layout)
        form_section.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(form_section, alignment=Qt.AlignmentFlag.AlignHCenter)

        # --- Submit Button ---
        submit_btn = QPushButton("✅ Submit Round Data")
        submit_btn.setFixedWidth(self.input_width)
        submit_btn.clicked.connect(self.save_input_only)
        layout.addWidget(submit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)

    def resizeEvent(self, event):
        # Set input width to 1/3 of the window width, min 200, max 400
        width = max(200, min(self.width() // 3, 400))
        for widget in self.inputs.values():
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.setFixedWidth(width)
        self.findChild(QPushButton).setFixedWidth(width)
        super().resizeEvent(event)

    def save_input_only(self):
        try:
            values = {}
            for k, widget in self.inputs.items():
                if isinstance(widget, QLineEdit):
                    text = widget.text()
                    # Try to convert to float, fallback to bool if possible
                    try:
                        values[k] = float(text)
                    except ValueError:
                        if text.lower() in ("true", "false"):
                            values[k] = text.lower() == "true"
                        else:
                            values[k] = text
                elif isinstance(widget, QComboBox):
                    val = widget.currentData()
                    # Convert 1/0 to True/False for boolean fields
                    if k in ["Pilot", "Legal Flight", "Good Landing", "Replacement Parts"]:
                        if val in (1, 0):
                            values[k] = bool(val)
                        else:
                            values[k] = val
                    else:
                        values[k] = val

            team_id, category = self.team_dropdown.currentData()
            team_id = str(team_id)  # Ensure string keys for JSON

            round_index, ok = QInputDialog.getInt(self, "Round Number", "Enter round number (starting from 0):", min=0)
            if not ok:
                return

            # Load results.json
            results = load_results()

            # Ensure category exists
            if category not in results:
                results[category] = {}
            # Ensure team exists
            if team_id not in results[category]:
                results[category][team_id] = []

            # Remove any existing round with the same round_index
            results[category][team_id] = [
                r for r in results[category][team_id] if r.get("round") != round_index
            ]

            # Add the new round data (score will be added later)
            results[category][team_id].append({
                "inputs": values,
                "round": round_index
            })

            # Save back to results.json
            with open("data/results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Saved", "Round input data saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid input: {e}")

# Add this import at the top of your file:
