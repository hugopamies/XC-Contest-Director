from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QMessageBox
from utils.storage import load_results, save_results, get_team_scores, delete_score, update_score
import json
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

class EditScoresTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.category_dropdown = QComboBox()
        self.category_dropdown.addItems(["Academic", "Clubs"])
        self.category_dropdown.currentIndexChanged.connect(self.load_teams)

        self.team_dropdown = QComboBox()
        self.team_dropdown.currentIndexChanged.connect(self.load_scores)
        self.score_list = QListWidget()


        self.delete_button = QPushButton("Delete Selected Score")
        self.delete_button.clicked.connect(self.delete_selected_score)

        self.layout.addWidget(QLabel("Category"))
        self.layout.addWidget(self.category_dropdown)
        self.layout.addWidget(QLabel("Team"))
        self.layout.addWidget(self.team_dropdown)
        self.layout.addWidget(QLabel("Scores"))
        self.layout.addWidget(self.score_list)

        # Add refresh button
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.delete_button)

        self.edit_button = QPushButton("Edit Selected Round Data")
        self.edit_button.clicked.connect(self.edit_selected_score)
        self.layout.addWidget(self.edit_button)



        self.setLayout(self.layout)

        self.teams = {}
        self.load_teams()

    def load_teams(self):
        cat = self.category_dropdown.currentText()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            all_teams = json.load(f)
        self.teams = {str(team["id"]): team["name"] for team in all_teams[cat]}
        self.team_dropdown.clear()
        for tid, name in self.teams.items():
            self.team_dropdown.addItem(f"{tid} - {name}", tid)
        self.load_scores()

    def load_scores(self):
        cat = self.category_dropdown.currentText()
        tid = self.team_dropdown.currentData()
        self.score_list.clear()
        if tid:
            scores = get_team_scores(tid, cat)
            for i, score in enumerate(scores):
                label = f"Round {i + 1}"
                if isinstance(score, dict) and "score" in score:
                    label += f": {score['score']:.2f}"
                self.score_list.addItem(label)

    def delete_selected_score(self):
        selected = self.score_list.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "No Selection", "Please select a score to delete.")
            return
        cat = self.category_dropdown.currentText()
        tid = self.team_dropdown.currentData()
        confirm = QMessageBox.question(self, "Confirm", "Delete selected score?")
        if confirm.name == "Yes":
            if delete_score(tid, cat, selected):
                QMessageBox.information(self, "Deleted", "Score deleted.")
                self.load_scores()
            else:
                QMessageBox.critical(self, "Error", "Could not delete score.")

    def edit_selected_score(self):
        selected_index = self.score_list.currentRow()
        if selected_index == -1:
            QMessageBox.warning(self, "No Selection", "Please select a score to edit.")
            return

        cat = self.category_dropdown.currentText()
        tid = self.team_dropdown.currentData()
        scores = get_team_scores(tid, cat)
        entry = scores[selected_index]

        if not isinstance(entry, dict) or "inputs" not in entry:
            QMessageBox.warning(self, "Unsupported", "Only scores with saved input data can be edited.")
            return

        original_inputs = entry["inputs"]

        # --- Build edit dialog ---
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Round Inputs")
        form = QFormLayout(dialog)

        fields = {}
        for k, v in original_inputs.items():
            le = QLineEdit(str(v))
            form.addRow(k, le)
            fields[k] = le

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addWidget(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec():
            try:
                new_inputs = {}
                for k, widget in fields.items():
                    val = widget.text().strip()
                    if val.lower() in ["true", "yes", "1"]:
                        new_inputs[k] = True
                    elif val.lower() in ["false", "no", "0"]:
                        new_inputs[k] = False
                    else:
                        new_inputs[k] = float(val)

                updated_entry = {
                    "inputs": new_inputs,
                    "round": entry.get("round", selected_index)
                }

                update_score(tid, cat, selected_index, updated_entry)
                QMessageBox.information(self, "Updated", "Round data updated successfully.")
                self.load_scores()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid input: {e}")

    def refresh_data(self):
        self.load_teams()
