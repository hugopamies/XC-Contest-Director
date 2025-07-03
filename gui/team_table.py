from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QTabWidget, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QFormLayout
from PyQt6.QtCore import Qt
import json
from utils.storage import load_results, save_results
from scoring.scoring_engine import total_score, compute_round_score, get_best_values_per_round
from utils.pdf_exporter import export_rankings_to_pdf
from utils.xlsx_exporter import export_all_data_to_excel
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QWidget as QtWidget
from PyQt6.QtGui import QFont

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, number):
        super().__init__(text)
        self.number = number
        self.setFont(QFont("Arial", 12))

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.number < other.number
        return super().__lt__(other)


class TeamRankingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 12))

        self.tabs.addTab(self.create_ranking_tab("Academic"), "Academic Rankings")
        self.tabs.addTab(self.create_ranking_tab("Clubs"), "Clubs Rankings")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)


        export_excel_btn = QPushButton("Export Scores to Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        export_excel_btn.setFont(QFont("Arial", 12))
        export_excel_btn.setSizePolicy(export_excel_btn.sizePolicy().horizontalPolicy(), export_excel_btn.sizePolicy().verticalPolicy())
        export_excel_btn.setMaximumWidth(export_excel_btn.fontMetrics().horizontalAdvance(export_excel_btn.text()) + 32)

        layout.addWidget(export_excel_btn)

        self.setLayout(layout)

    def create_ranking_tab(self, category):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        table = QTableWidget()
        table.setStyleSheet("font-size: 12px; font-family: Arial;")
        table.setFont(QFont("Arial", 12))
        table.setObjectName("rankingsTable")

        # Remove row labels
        table.verticalHeader().setVisible(False)

        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()
        static_scores = results.get("static_scores", {}).get(category, {})
        penalties = results.get("penalties", {}).get(category, {})
        penalty_reasons = results.get("penalty_reasons", {}).get(category, {})

        all_scores = []
        max_rounds = 0

        for team in teams[category]:
            tid = str(team["id"])
            rounds = results.get(category, {}).get(tid, [])
            all_scores.append((team, rounds))
            max_rounds = max(max_rounds, len(rounds))

        # Calculate total scores for ranking
        team_totals = []
        for team, rounds in all_scores:
            tid = str(team["id"])
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
                    score = float(r) if isinstance(r, (int, float)) else 0
                    recalculated_scores.append(score)
            if category == "Academic":
                static_score = static_scores.get(tid, 250)
            else:
                static_score = 0
            penalty = penalties.get(tid, 0)
            # Exclude R0 (static/penalty) from total score calculation
            total = total_score(recalculated_scores) + static_score - penalty if recalculated_scores else static_score - penalty
            team_totals.append((tid, total))

        # Sort teams by total score descending for ranking
        sorted_team_totals = sorted(team_totals, key=lambda x: x[1], reverse=True)
        tid_to_rank = {tid: rank + 1 for rank, (tid, _) in enumerate(sorted_team_totals)}

        # Add "Rank" column to the left, and "#" before Team ID
        # Add "R0" column before round columns
        # Add "Total (1)", "Total (1-2)", ..., "Total (1-n)" columns after round columns
        total_columns = [f"Score After R{i+1}" for i in range(max_rounds)]
        if category == "Academic":
            headers = (
                ["Rank", "Team ID", "Team Name", "Organization", "Static", "Penalties", "R0"]
                + [f"R{i+1}" for i in range(max_rounds)]
                + total_columns
                + ["Reason for Penalties"]
            )
            static_col_offset = 1
        else:
            headers = (
                ["Rank", "Team ID", "Team Name", "Organization", "Penalties", "R0"]
                + [f"R{i+1}" for i in range(max_rounds)]
                + total_columns
                + ["Reason for Penalties"]
            )
            static_col_offset = 0
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSortingEnabled(True)
        table.setRowCount(len(all_scores))

        # Set header font: Bold Arial 13
        header = table.horizontalHeader()
        header_font = QFont("Arial", 13)
        header_font.setBold(True)
        header.setFont(header_font)

        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)

        for row, (team, rounds) in enumerate(all_scores):
            tid = str(team["id"])
            name = team["name"]
            organization = team.get("organization", "")
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

            if category == "Academic":
                static_score = static_scores.get(tid, 250)
            else:
                static_score = 0
            penalty = penalties.get(tid, 0)
            penalty_reason = penalty_reasons.get(tid, "")
            # R0 is static - penalty (for clubs, static_score is 0)
            r0_score = static_score - penalty

            # Exclude R0 from total score calculation
            total = total_score(recalculated_scores) + static_score - penalty if recalculated_scores else static_score - penalty

            # Rank column (bold)
            rank = tid_to_rank.get(tid, "")
            rank_item = NumericTableWidgetItem(str(rank), rank if isinstance(rank, int) else 0)
            font = QFont("Arial", 12)
            font.setBold(True)
            rank_item.setFont(font)
            table.setItem(row, 0, rank_item)

            # Team ID column with "#"
            item_id = NumericTableWidgetItem(f"#{tid}", int(tid))
            item_id.setFont(QFont("Arial", 12))
            table.setItem(row, 1, item_id)
            table.setItem(row, 2, QTableWidgetItem(str(name)))
            table.item(row, 2).setFont(QFont("Arial", 12))
            table.setItem(row, 3, QTableWidgetItem(str(organization)))
            table.item(row, 3).setFont(QFont("Arial", 12))

            col = 4
            if category == "Academic":
                static_item = NumericTableWidgetItem(str(static_score), static_score)
                static_item.setFont(QFont("Arial", 12))
                table.setItem(row, col, static_item)
                col += 1
            penalty_item = NumericTableWidgetItem(str(penalty), penalty)
            penalty_item.setFont(QFont("Arial", 12))
            table.setItem(row, col, penalty_item)
            col += 1

            # R0 column (static - penalty)
            r0_item = NumericTableWidgetItem(str(round(r0_score, 2)), r0_score)
            r0_item.setFont(QFont("Arial", 12))
            table.setItem(row, col, r0_item)
            col += 1

            # Round columns (R1, R2, ...)
            for i, score in enumerate(recalculated_scores):
                round_item = QTableWidgetItem(str(round(score, 2)))
                round_item.setFont(QFont("Arial", 12))
                table.setItem(row, col + i, round_item)
            # Fill empty rounds with blank
            for i in range(len(recalculated_scores), max_rounds):
                empty_item = QTableWidgetItem("")
                empty_item.setFont(QFont("Arial", 12))
                table.setItem(row, col + i, empty_item)
            col += max_rounds

            # Total columns for each round (exclude R0 in totals)
            for i in range(max_rounds):
                partial_total = total_score(recalculated_scores[:i+1]) + static_score - penalty
                item_total = NumericTableWidgetItem(str(round(partial_total, 2)), partial_total)
                total_font = QFont("Arial", 12)
                total_font.setBold(True)
                item_total.setFont(total_font)
                if i == max_rounds - 1:
                    item_total.setForeground(Qt.GlobalColor.red)
                table.setItem(row, col + i, item_total)
            col += max_rounds

            # Reason for Penalties column (last)
            reason_item = QTableWidgetItem(str(penalty_reason))
            reason_item.setFont(QFont("Arial", 12))
            table.setItem(row, col, reason_item)

        save_results(results)

        table.resizeColumnsToContents()

        label = QLabel(f"{category.capitalize()} Team Rankings")
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        layout.addWidget(table)

        # Add column visibility controls
        column_control_layout = QVBoxLayout()

        column_checkboxes = []
        column_control_widget = QtWidget()
        column_control_hbox = QHBoxLayout()
        column_control_hbox.setContentsMargins(0, 0, 0, 0)

        def make_toggle_handler(col_idx):
            def handler(state):
                table.setColumnHidden(col_idx, not bool(state))
            return handler

        for idx, header in enumerate(headers):
            cb = QCheckBox(header)
            cb.setFont(QFont("Arial", 12))
            cb.setChecked(True)
            cb.stateChanged.connect(make_toggle_handler(idx))
            column_checkboxes.append(cb)
            column_control_hbox.addWidget(cb)
        column_control_widget.setLayout(column_control_hbox)
        layout.addWidget(column_control_widget)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(lambda: self.rebuild_tab(category, widget))
        refresh_btn.setFont(QFont("Arial", 12))
        refresh_btn.setMaximumWidth(refresh_btn.fontMetrics().horizontalAdvance(refresh_btn.text()) + 32)
        layout.addWidget(refresh_btn)

        if category == "Academic":
            edit_static_btn = QPushButton("🛠️ Edit Static Scores")
            edit_static_btn.clicked.connect(self.edit_static_scores)
            edit_static_btn.setFont(QFont("Arial", 12))
            edit_static_btn.setMaximumWidth(edit_static_btn.fontMetrics().horizontalAdvance(edit_static_btn.text()) + 32)
            layout.addWidget(edit_static_btn)

            edit_penalty_btn = QPushButton("⚖️ Edit Penalties")
            edit_penalty_btn.clicked.connect(self.edit_penalties_and_reasons)
            edit_penalty_btn.setFont(QFont("Arial", 12))
            edit_penalty_btn.setMaximumWidth(edit_penalty_btn.fontMetrics().horizontalAdvance(edit_penalty_btn.text()) + 32)
            layout.addWidget(edit_penalty_btn)

        widget.setLayout(layout)
        table.sortItems(len(headers) - 2, Qt.SortOrder.DescendingOrder)
        return widget

    def edit_static_scores(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Static Scores")

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        table.setFont(QFont("Arial", 12))
        # Remove row labels
        table.verticalHeader().setVisible(False)

        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()
        static_scores = results.setdefault("static_scores", {}).setdefault("Academic", {})

        academic_teams = teams["Academic"]
        table.setRowCount(len(academic_teams))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Team Name", "Static Score"])
        # Header font: Bold Arial 13
        header_font = QFont("Arial", 13)
        header_font.setBold(True)
        table.horizontalHeader().setFont(header_font)
        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)

        for row, team in enumerate(academic_teams):
            name = team["name"]
            tid = str(team["id"])
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont("Arial", 12))
            table.setItem(row, 0, name_item)
            score_item = QTableWidgetItem(str(static_scores.get(tid, 250)))
            score_item.setFont(QFont("Arial", 12))
            table.setItem(row, 1, score_item)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setFont(QFont("Arial", 12))
        layout.addWidget(buttons)

        buttons.accepted.connect(lambda: self.save_static_scores(table, teams["Academic"], dialog))
        buttons.rejected.connect(dialog.reject)

        dialog.exec()

    def edit_penalties_and_reasons(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Penalties & Reasons")

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        table.setFont(QFont("Arial", 12))
        table.verticalHeader().setVisible(False)

        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)

        results = load_results()
        penalties = results.setdefault("penalties", {}).setdefault("Academic", {})
        penalty_reasons = results.setdefault("penalty_reasons", {}).setdefault("Academic", {})

        academic_teams = teams["Academic"]
        table.setRowCount(len(academic_teams))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Team Name", "Penalties", "Reason for Penalties"])
        # Header font: Bold Arial 13
        header_font = QFont("Arial", 13)
        header_font.setBold(True)
        table.horizontalHeader().setFont(header_font)
        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)

        for row, team in enumerate(academic_teams):
            name = team["name"]
            tid = str(team["id"])
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont("Arial", 12))
            table.setItem(row, 0, name_item)
            penalty_item = QTableWidgetItem(str(penalties.get(tid, 0)))
            penalty_item.setFont(QFont("Arial", 12))
            table.setItem(row, 1, penalty_item)
            reason_item = QTableWidgetItem(str(penalty_reasons.get(tid, "")))
            reason_item.setFont(QFont("Arial", 12))
            table.setItem(row, 2, reason_item)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setFont(QFont("Arial", 12))
        layout.addWidget(buttons)

        buttons.accepted.connect(lambda: self.save_penalties_and_reasons(table, teams["Academic"], dialog))
        buttons.rejected.connect(dialog.reject)

        dialog.exec()

    def save_penalties_and_reasons(self, table, teams, dialog):
        results = load_results()
        for row, team in enumerate(teams):
            tid = str(team["id"])
            try:
                penalty = float(table.item(row, 1).text())
            except:
                penalty = 0
            reason = table.item(row, 2).text() if table.item(row, 2) else ""
            results.setdefault("penalties", {}).setdefault("Academic", {})[tid] = penalty
            results.setdefault("penalty_reasons", {}).setdefault("Academic", {})[tid] = reason
        save_results(results)
        dialog.accept()
        self.rebuild_tab("Academic", self.tabs.widget(0))

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
            rankings_data = self.get_all_rankings_data()
            export_rankings_to_pdf(filename, rankings_data)
            QMessageBox.information(self, "Export Complete", f"Exported to {filename}")

    def export_excel(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Excel", "XC_results.xlsx", "Excel Files (*.xlsx)")
        if filename:
            rankings_data = self.get_all_rankings_data()
            export_all_data_to_excel(filename, rankings_data)
            QMessageBox.information(self, "Export Complete", f"Exported to {filename}")

    def get_all_rankings_data(self):
        rankings_data = {}
        for i in range(self.tabs.count()):
            category = "Academic" if i == 0 else "Clubs"
            table = self.tabs.widget(i).findChild(QTableWidget, "rankingsTable")
            headers = [table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]
            rows = []
            for row in range(table.rowCount()):
                row_data = {}
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data[headers[col]] = item.text() if item else ""
                rows.append(row_data)
            rankings_data[category] = rows
        return rankings_data
