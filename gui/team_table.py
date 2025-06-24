from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QTabWidget, QFileDialog, QMessageBox
import json
from utils.storage import load_results
from scoring.scoring_engine import total_score
from utils.pdf_exporter import export_rankings_to_pdf
from utils.xlsx_exporter import export_all_data_to_excel
from scoring.scoring_engine import compute_round_score, get_best_values_per_round




class TeamRankingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()

        self.academic_tab = self.create_ranking_tab("Academic")
        self.clubs_tab = self.create_ranking_tab("Clubs")

        self.tabs.addTab(self.academic_tab, "Academic Rankings")
        self.tabs.addTab(self.clubs_tab, "Clubs Rankings")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

        export_pdf_btn = QPushButton("🖨️ Export to PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)

        export_excel_btn = QPushButton("🧾 Export to Excel")
        export_excel_btn.clicked.connect(self.export_excel)

        layout.addWidget(export_pdf_btn)
        layout.addWidget(export_excel_btn)

        self.setLayout(layout)

    def rebuild_tab(self, category, old_widget):
        new_tab = self.create_ranking_tab(category)
        index = self.tabs.indexOf(old_widget)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, new_tab, f"{category.capitalize()} Rankings")
        self.tabs.setCurrentIndex(index)

    def create_ranking_tab(self, category):
        widget = QWidget()
        layout = QVBoxLayout()
        table = QTableWidget()

        # ✅ LOAD teams and results HERE
        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()

        # Load all team scores and find max rounds
        all_scores = []
        max_rounds = 0

        for team in teams[category]:
            tid = str(team["id"])
            rounds = results.get(category, {}).get(tid, [])
            all_scores.append((team, rounds))
            max_rounds = max(max_rounds, len(rounds))

        table.setColumnCount(2 + max_rounds + 1)  # ID, Name, R1...Rn, Total
        headers = ["Team ID", "Team Name"] + [f"R{i+1}" for i in range(max_rounds)] + ["Total Score"]
        table.setHorizontalHeaderLabels(headers)

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
                else:
                    # Fallback: keep legacy or simple float score
                    recalculated_scores.append(float(r) if isinstance(r, (int, float)) else 0)

            

        
            total = total_score(recalculated_scores)


            table.setItem(row, 0, QTableWidgetItem(tid))
            table.setItem(row, 1, QTableWidgetItem(name))

            for i, score in enumerate(recalculated_scores):

                table.setItem(row, 2 + i, QTableWidgetItem(str(round(score, 2))))

            table.setItem(row, 2 + max_rounds, QTableWidgetItem(str(round(total, 2))))

        layout.addWidget(QLabel(f"{category.capitalize()} Team Rankings"))
        layout.addWidget(table)
        refresh_btn = QPushButton("🔄 Refresh Rankings")
        refresh_btn.clicked.connect(lambda: self.rebuild_tab(category, widget))
        layout.addWidget(refresh_btn)

        widget.setLayout(layout)
        return widget

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
