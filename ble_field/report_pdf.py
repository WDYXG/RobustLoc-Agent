"""Render the stage report with an embedded Chinese font."""
import argparse
import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render(source, output, font):
    pdfmetrics.registerFont(TTFont("ReportChinese", str(font)))
    ink = colors.HexColor("#16313b")
    blue = colors.HexColor("#166c70")
    body = ParagraphStyle("Body", fontName="ReportChinese", fontSize=10.5, leading=17,
                          textColor=ink, wordWrap="CJK", spaceAfter=8, alignment=TA_LEFT)
    heading = ParagraphStyle("Heading", parent=body, fontSize=15, leading=23, textColor=blue,
                             spaceBefore=11, spaceAfter=6, keepWithNext=True)
    title = ParagraphStyle("Title", parent=heading, fontSize=26, leading=34,
                           spaceAfter=7, textColor=ink)
    cell = ParagraphStyle("Cell", parent=body, fontSize=9.5, leading=15, spaceAfter=0)
    doc = SimpleDocTemplate(str(output), pagesize=A4, topMargin=54, bottomMargin=49,
                            leftMargin=47, rightMargin=47, title="RobustLoc 众包 BLE 静态实测准备")
    story, rows = [], []

    def flush():
        if not rows:
            return
        table = Table(rows[:], colWidths=[105, doc.width - 105], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeceb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f7f7")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#b3cdcd")),
        ]))
        story.extend((table, Spacer(1, 8)))
        rows.clear()

    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("|"):
            columns = [s.strip() for s in line.strip("|").split("|")]
            if not all(set(c) <= {"-", ":", " "} for c in columns):
                rows.append([Paragraph(html.escape(c), cell) for c in columns])
            continue
        flush()
        if line.startswith("# "):
            story.append(Paragraph(html.escape(line[2:]), title))
        elif line.startswith("## "):
            story.append(Paragraph(html.escape(line[3:]), heading))
        elif line:
            story.append(Paragraph(html.escape(line), body))
    flush()

    def page(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(blue)
        canvas.setLineWidth(1.2)
        canvas.line(47, A4[1] - 38, A4[0] - 47, A4[1] - 38)
        canvas.setFont("ReportChinese", 8.5)
        canvas.setFillColor(blue)
        canvas.drawString(47, 29, "RobustLoc-Agent  /  静态实地验证")
        canvas.drawRightString(A4[0] - 47, 29, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=page, onLaterPages=page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font", type=Path, default=Path("C:/Windows/Fonts/simhei.ttf"))
    args = parser.parse_args()
    render(args.source, args.output, args.font)
