from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
import json
from utils.storage import load_results
from scoring.scoring_engine import compute_round_score, get_best_values_per_round
import math
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QFileDialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from PyQt6.QtWidgets import QFileDialog
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, number):
        super().__init__(text)
        self.number = number

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.number < other.number
        return super().__lt__(other)


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

        self.export_pdf_btn = QPushButton("📄 Export to PDF")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_btn)

        self.export_excel_btn = QPushButton("📊 Export to Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        self.layout.addWidget(self.export_excel_btn)


    def refresh_data(self):
        # Load teams
        category = self.category_dropdown.currentText()
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
            tab.setLayout(layout)
            self.round_tabs.addTab(tab, f"Round {round_index + 1}")

            self.populate_table(table, category, round_index)


    def populate_table(self, table, category, round_index):
        headers = [
            "Rank",  # New column for ranking
            "Team ID", "Team Name", "Organization",  # Added Organization column
            "Payload", "Circuit", "Glide",
            "Loading", "Altitude", "Flight Score",
            "Takeoff", "Pilot", "Legal", "Landing", "Repl. Parts"
        ]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.teams))
        table.setSortingEnabled(False)  # We'll enable it later after filling it

        # Remove row labels (numbers 1,2,3...) by hiding the vertical header
        table.verticalHeader().setVisible(False)

        # Load best values for the round
        best_Cdes, best_Tcarga, best_Tcircuit, best_Tglide = get_best_values_per_round(
            self.results, category, round_index
        )
        best_eff = best_Cdes / (best_Tcarga ** 0.5) if best_Tcarga > 0 else 1

        # Prepare list to compute rankings
        team_scores = []

        for row, team in enumerate(self.teams):
            tid = str(team["id"])
            name = team["name"]
            organization = team.get("organization", "")  # Read organization, allow special chars

            team_rounds = self.results.get(category, {}).get(tid, [])
            if round_index >= len(team_rounds):
                values = ["0.00"] * 6 + ["0.00"]  # all subscores + total
                total = 0.0
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
                    "Academic": {
                        "payload": 150,
                        "circuit": 150,
                        "glide": 100,
                        "altitude": 100,
                        "loading": 100
                    },
                    "Clubs": {
                        "payload": 200,
                        "circuit": 200,
                        "glide": 150,
                        "altitude": 150,
                        "loading": 100
                    }
                }

                w = weights.get(category, weights["Academic"])

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
                
                if category == "Academic":
                    altitude_score = 4.3636e-6 * (A60s ** 4) - 0.001215 * (A60s ** 3) + 0.095732 * (A60s ** 2) - 0.86741 * A60s
                    altitude_score = math.ceil(altitude_score * 10) / 10
                elif category == "Clubs":
                    altitude_score = 6.5455e-6 * (A60s ** 4) - 0.001822 * (A60s ** 3) + 0.1436 * (A60s ** 2) - 1.3011 * A60s
                    altitude_score = math.ceil(altitude_score * 10) / 10
                else:
                    altitude_score = 0
                

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

                takeoff = inputs.get("Takeoff Distance", "-")
                if isinstance(takeoff, (int, float)):
                    takeoff = str(int(round(takeoff)))
                pilot = "Team" if inputs.get("Pilot") else "External"
                legal = "✔️" if inputs.get("Legal Flight") else "❌"
                landing = "✔️" if inputs.get("Good Landing") else "❌"
                replacements = "No" if inputs.get("Replacement Parts") else "Yes"

                values += [str(takeoff), pilot, legal, landing, replacements]

            # Save for ranking
            team_scores.append({
                "row": row,
                "total": float(values[5]) if len(values) > 5 else 0.0,  # total score is at index 5
            })

            # Fill table row (leave rank for now, fill after sorting)
            table.setItem(row, 1, NumericTableWidgetItem(tid, int(tid)))
            table.setItem(row, 2, QTableWidgetItem(str(name)))
            table.setItem(row, 3, QTableWidgetItem(str(organization)))  # Organization column, supports special chars
            for col, val in enumerate(values, start=4):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col == 9:  # Total Score column (index 9 from start=4)
                    item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    item.setForeground(QColor("#228B22"))  # Forest Green
                elif 4 <= col <= 8:  # Payload to Altitude (core scoring)
                    item.setFont(QFont("Arial", 9, QFont.Weight.DemiBold))
                elif col >= 10:  # Extra fields
                    item.setFont(QFont("Arial", 8))
                    item.setForeground(QColor("#888888"))  # Dim gray

                table.setItem(row, col, item)

        # Compute ranking based on total score (descending)
        sorted_scores = sorted(team_scores, key=lambda x: x["total"], reverse=True)
        rank_map = {}
        current_rank = 1
        last_score = None
        for idx, entry in enumerate(sorted_scores):
            score = entry["total"]
            if last_score is not None and score < last_score:
                current_rank = idx + 1
            rank_map[entry["row"]] = current_rank
            last_score = score

        # Fill in the rank column
        for row in range(len(self.teams)):
            rank_item = QTableWidgetItem(str(rank_map[row]))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            table.setItem(row, 0, rank_item)

        table.horizontalHeaderItem(9).setFont(QFont("Arial", 10, QFont.Weight.Bold))
        table.horizontalHeaderItem(9).setForeground(QColor("#228B22"))

        table.resizeColumnsToContents()
        table.setSortingEnabled(True)

        # Set all row heights to the same value for uniformity
        uniform_height = 32  # You can adjust this value as needed
        for row in range(table.rowCount()):
            table.setRowHeight(row, uniform_height)
 
    def export_to_pdf(self):

        filename, _ = QFileDialog.getSaveFileName(self, "Export Round Details to PDF", "round_details.pdf", "PDF Files (*.pdf)")
        if not filename:
            return

        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        category = self.category_dropdown.currentText()

        for tab_index in range(self.round_tabs.count()):
            tab = self.round_tabs.widget(tab_index)
            table_widget = tab.findChild(QTableWidget)

            # Round title
            title = Paragraph(f"<b>{category} - Round {tab_index + 1}</b>", styles["Heading2"])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Extract headers
            headers = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]
            data = [headers]

            # Extract rows
            for row in range(table_widget.rowCount()):
                row_data = []
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Build ReportLab Table
            pdf_table = Table(data, repeatRows=1, hAlign='LEFT')
            pdf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#B50220")),  # header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f9f9f9"), colors.HexColor("#ffffff")])
            ]))

            elements.append(pdf_table)
            elements.append(PageBreak())

        doc.build(elements)

    def export_to_excel(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Round Details to Excel", "round_details.xlsx", "Excel Files (*.xlsx)")
        if not filename:
            return

        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet

        for tab_index in range(self.round_tabs.count()):
            tab = self.round_tabs.widget(tab_index)
            table = tab.findChild(QTableWidget)

            sheet_title = f"Round_{tab_index + 1}"
            ws = wb.create_sheet(title=sheet_title)

            # Headers
            for col in range(table.columnCount()):
                header = table.horizontalHeaderItem(col).text()
                ws.cell(row=1, column=col+1, value=header)

            # Rows
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    text = item.text() if item else ""
                    ws.cell(row=row+2, column=col+1, value=text)

            # Auto width
            for col in range(1, table.columnCount() + 1):
                ws.column_dimensions[get_column_letter(col)].width = 16

        wb.save(filename)
