from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from utils.storage import load_results
from scoring.scoring_engine import total_score
import json

def export_rankings_to_pdf(filename="rankings.pdf"):
    with open("data/teams.json", "r", encoding="utf-8") as f:
        teams = json.load(f)
    results = load_results()

    data = [["Team ID", "Team Name", "Category", "Total Score"]]
    combined = []

    for category in ["academic", "clubs"]:
        for team in teams[category]:
            tid = str(team["id"])
            rounds = results.get(category, {}).get(tid, [])
            score = total_score(rounds)
            combined.append((int(tid), team["name"], category.capitalize(), round(score, 2)))

    combined.sort(key=lambda x: x[3], reverse=True)
    data += combined

    doc = SimpleDocTemplate(filename, pagesize=A4)
    style = getSampleStyleSheet()
    elements = [Paragraph("UAV Competition Rankings", style['Title'])]

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
