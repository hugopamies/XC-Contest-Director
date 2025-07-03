from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_rankings_to_pdf(filepath, rankings_data):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Team Rankings")
    y -= 30

    for category, rows in rankings_data.items():
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, f"{category} Rankings")
        y -= 20

        if not rows:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(margin, y, "No data available.")
            y -= 30
            continue

        headers = list(rows[0].keys())
        c.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            c.drawString(margin + i * 100, y, header)
        y -= 20

        c.setFont("Helvetica", 8)
        for row in rows:
            if y < margin:
                c.showPage()
                y = height - margin
            for i, header in enumerate(headers):
                text = row[header]
                c.drawString(margin + i * 100, y, text)
            y -= 15

        y -= 30  # space between categories

    c.save()

