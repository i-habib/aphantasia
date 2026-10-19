"""Render the editable P5 working manuscript as a readable review PDF.

Requires reportlab. Does not read participant data.
"""
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import letter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "projects/P5_asd_adhd_replication/submission"
OUT = ROOT / "output/pdf/p5_submission_review.pdf"


def fmt(text):
    """Escape text for reportlab and turn **bold** into <b>bold</b>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(text))


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyP5", fontName="Helvetica", fontSize=10.2, leading=14.3,
                              spaceAfter=8, textColor=colors.HexColor("#252d35")))
    styles.add(ParagraphStyle(name="BulletP5", parent=styles["BodyP5"], leftIndent=11, firstLineIndent=-7))
    styles.add(ParagraphStyle(name="CellP5", parent=styles["BodyP5"], fontSize=7.5, leading=9.5, spaceAfter=0))
    styles["Title"].fontSize = 20
    styles["Title"].leading = 24
    styles["Title"].alignment = TA_LEFT
    styles["Title"].textColor = colors.HexColor("#245b87")
    for name in ["Heading1", "Heading2"]:
        styles[name].textColor = colors.HexColor("#245b87")
        styles[name].spaceBefore = 13
        styles[name].spaceAfter = 7
        styles[name].keepWithNext = True
    styles.add(ParagraphStyle(name="CaptionP5", parent=styles["BodyP5"], fontSize=8.8, leading=12))
    styles.add(ParagraphStyle(name="TableTitleP5", parent=styles["BodyP5"], fontName="Helvetica-Bold", keepWithNext=True, spaceBefore=6))
    story = []
    text = (SOURCE / "manuscript_working.md").read_text()
    text += "\n\n[P5_APPENDIX]\n\n" + (SOURCE / "supplement.md").read_text()
    # [INCLUDE file.md] pulls in a generated table; [FIGURE file.png | caption] places a figure.
    text = re.sub(r"^\[INCLUDE ([^\]]+)\]$", lambda m: (SOURCE / m.group(1)).read_text(), text, flags=re.M)
    for block in text.split("\n\n"):
        block = block.strip()
        if not block: continue
        if block == "[P5_APPENDIX]":
            story.append(PageBreak())
            continue
        if block.startswith("[FIGURE "):
            name, caption = [part.strip() for part in block[len("[FIGURE "):-1].split("|", 1)]
            width, height = ImageReader(str(SOURCE / name)).getSize()
            story.append(KeepTogether([Image(str(SOURCE / name), width=468, height=468 * height / width),
                                       Paragraph(escape(caption), styles["CaptionP5"]), Spacer(1, 8)]))
            continue
        if block.startswith("| "):
            data = []
            for line in block.splitlines():
                if set(line.replace("|", "").replace(":", "").replace(" ", "")) <= {"-"}: continue
                data.append([Paragraph(escape(v.strip()), styles["CellP5"]) for v in line.strip("|").split("|")])
            n = len(data[0])
            first = 492 * (0.42 if n <= 3 else 0.34 if n == 4 else 0.28)
            widths = [first] + [(492 - first) / (n - 1)] * (n - 1)
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9eff4")),
                ("VALIGN", (0,0), (-1,-1), "TOP"), ("LINEBELOW", (0,0), (-1,0), .6, colors.HexColor("#a7b7c5")),
                ("LINEBELOW", (0,1), (-1,-1), .2, colors.HexColor("#d6dde2")),
                ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
            heading = []
            if story and isinstance(story[-1], Paragraph) and story[-1].style.name in {"Heading1", "Heading2", "TableTitleP5"}:
                heading = [story.pop()]
            story += [KeepTogether([*heading, table, Spacer(1, 10)])]
            continue
        if block.startswith("Table ") and "\n" not in block and len(block) < 120:
            story.append(Paragraph(escape(block), styles["TableTitleP5"]))
            continue
        if block.startswith("# "):
            story.append(Paragraph(escape(block[2:]), styles["Title"]))
        elif block.startswith("### "):
            story.append(Paragraph(escape(block[4:]), styles["Heading2"]))
        elif block.startswith("## "):
            story.append(Paragraph(escape(block[3:]), styles["Heading1"]))
        elif re.match(r"(- |\d+\. )", block):
            for line in block.splitlines():
                marker = re.match(r"(\s*)(- |\d+\. )?(.*)", line)
                indent = 11 + 14 * (len(marker.group(1)) // 2)
                style = ParagraphStyle(name=f"List{indent}", parent=styles["BulletP5"], leftIndent=indent)
                story.append(Paragraph((marker.group(2) or "").replace("- ", "• ") + fmt(marker.group(3)), style))
        else:
            story.append(Paragraph(fmt(block).replace("\n", " "), styles["BodyP5"]))
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#d6dde2")); canvas.line(54, 43, 558, 43)
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#65727d"))
        canvas.drawString(54, 30, "P5 working copy | 18 October 2026 | author sections and declarations incomplete")
        canvas.drawRightString(558, 30, str(doc.page))
    SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=48,
                      bottomMargin=56, title="P5 manuscript working copy and submission review", author="Ivan Habib").build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
