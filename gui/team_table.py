from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QTabWidget, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QFormLayout
from PyQt6.QtCore import Qt
import json
from utils.storage import load_results, save_results
from scoring.scoring_engine import total_score, compute_round_score, get_best_values_per_round
from utils.pdf_exporter import export_rankings_to_pdf
from utils.xlsx_exporter import export_all_data_to_excel

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, number):
        super().__init__(text)
        self.number = number

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.number < other.number
        return super().__lt__(other)


class TeamRankingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_ranking_tab("Academic"), "Academic Rankings")
        self.tabs.addTab(self.create_ranking_tab("Clubs"), "Clubs Rankings")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

        export_pdf_btn = QPushButton("🖨️ Export to PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)

        export_excel_btn = QPushButton("🧾 Export to Excel")
        export_excel_btn.clicked.connect(self.export_excel)

        layout.addWidget(export_pdf_btn)
        layout.addWidget(export_excel_btn)

        self.setLayout(layout)

    def create_ranking_tab(self, category):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        table = QTableWidget()
        table.setStyleSheet("font-size: 18px;")

        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()
        static_scores = results.get("static_scores", {}).get(category, {})

        all_scores = []
        max_rounds = 0

        for team in teams[category]:
            tid = str(team["id"])
            rounds = results.get(category, {}).get(tid, [])
            all_scores.append((team, rounds))
            max_rounds = max(max_rounds, len(rounds))

        table.setColumnCount(3 + max_rounds + 1)
        headers = ["Team ID", "Team Name", "Static"] + [f"R{i+1}" for i in range(max_rounds)] + ["Total Score"]
        table.setHorizontalHeaderLabels(headers)
        table.setSortingEnabled(True)
        table.setRowCount(len(all_scores))

        for row, (team, rounds) in enumerate(all_scores):
            tid = str(team["id"])
            name = team["name"]
            recalculated_scores = []

            for i, r in enumerate(rounds):
                if isinstance(r, dict) and "inputs" in r:
                    inputs = r["inputs"]
                    best_Cdes, best_Tcarga, best_Tcircuit, best_Tglide = get_best_values_per_round(results, category, i)
                    score = compute_round_score(
                        inputs, category,
                        best_unloaded_payload=best_Cdes,
                        best_loading_time=best_Tcarga,
                        best_circuit_time=best_Tcircuit,
                        best_glide_time=best_Tglide
                    )
                    recalculated_scores.append(score)
                    r["score"] = score
                    r["inputs"] = inputs
                    r["round"] = i
                else:
                    score = float(r) if isinstance(r, (int, float)) else 0
                    recalculated_scores.append(score)
                    results[category][tid][i] = {
                        "inputs": {},
                        "score": score,
                        "round": i
                    }

            static_score = static_scores.get(tid, 250)
            total = total_score(recalculated_scores) + static_score

            item_id = NumericTableWidgetItem(tid, int(tid))
            table.setItem(row, 0, item_id)
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, NumericTableWidgetItem(str(static_score), static_score))

            for i, score in enumerate(recalculated_scores):
                table.setItem(row, 3 + i, QTableWidgetItem(str(round(score, 2))))

            item_total = NumericTableWidgetItem(str(round(total, 2)), total)
            table.setItem(row, 3 + max_rounds, item_total)

        save_results(results)

        table.resizeColumnsToContents()

        layout.addWidget(QLabel(f"{category.capitalize()} Team Rankings"))
        layout.addWidget(table)

        refresh_btn = QPushButton("🔄 Refresh Rankings")
        refresh_btn.clicked.connect(lambda: self.rebuild_tab(category, widget))
        layout.addWidget(refresh_btn)

        if category == "Academic":
            edit_static_btn = QPushButton("🛠️ Edit Static Scores")
            edit_static_btn.clicked.connect(self.edit_static_scores)
            layout.addWidget(edit_static_btn)

        widget.setLayout(layout)
        table.sortItems(3 + max_rounds, Qt.SortOrder.DescendingOrder)
        return widget

    def edit_static_scores(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Static Scores")

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()
        static_scores = results.setdefault("static_scores", {}).setdefault("Academic", {})

        academic_teams = teams["Academic"]
        table.setRowCount(len(academic_teams))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Team Name", "Static Score"])

        for row, team in enumerate(academic_teams):
            name = team["name"]
            tid = str(team["id"])
            table.setItem(row, 0, QTableWidgetItem(name))
            score_item = QTableWidgetItem(str(static_scores.get(tid, 250)))
            table.setItem(row, 1, score_item)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(lambda: self.save_static_scores(table, teams["Academic"], dialog))
        buttons.rejected.connect(dialog.reject)

        dialog.exec()

    def save_static_scores(self, table, teams, dialog):
        results = load_results()
        for row, team in enumerate(teams):
            tid = str(team["id"])
            try:
                score = float(table.item(row, 1).text())
            except:
                score = 0
            results.setdefault("static_scores", {}).setdefault("Academic", {})[tid] = score
        save_results(results)
        dialog.accept()
        self.rebuild_tab("Academic", self.tabs.widget(0))

    def rebuild_tab(self, category, old_widget):
        new_tab = self.create_ranking_tab(category)
        index = self.tabs.indexOf(old_widget)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, new_tab, f"{category.capitalize()} Rankings")
        self.tabs.setCurrentIndex(index)

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF", "rankings.pdf", "PDF Files (*.pdf)")
        if filename:
            export_rankings_to_pdf(filename)
            QMessageBox.information(self, "Export Complete", f"Exported to {filename}")

    def export_excel(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Excel", "uav_results.xlsx", "Excel Files (*.xlsx)")
        if filename:
            export_all_data_to_excel(filename)
            QMessageBox.information(self, "Export Complete", f"Exported to {filename}")
