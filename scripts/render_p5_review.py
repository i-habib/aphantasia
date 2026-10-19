"""Render the editable P5 working manuscript as a readable review PDF.

Requires reportlab. Does not read participant data.
"""
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="cortex/manuscript_cortex.md", help="manuscript file inside the submission folder")
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--footer", default="P5 working copy | author sections and declarations incomplete")
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Plain manuscript style: Times 12 pt, double-spaced body, black bold headings.
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyP5", fontName="Times-Roman", fontSize=12, leading=24,
                              spaceAfter=0, firstLineIndent=24, textColor=colors.black))
    styles.add(ParagraphStyle(name="BulletP5", parent=styles["BodyP5"], leftIndent=24, firstLineIndent=-12))
    styles.add(ParagraphStyle(name="CellP5", parent=styles["BodyP5"], fontSize=9, leading=11, firstLineIndent=0))
    styles["Title"].fontName = "Times-Bold"
    styles["Title"].fontSize = 16
    styles["Title"].leading = 22
    styles["Title"].textColor = colors.black
    styles["Title"].alignment = TA_CENTER
    for name, size in [("Heading1", 13), ("Heading2", 12)]:
        styles[name].fontName = "Times-Bold" if name == "Heading1" else "Times-BoldItalic"
        styles[name].fontSize = size
        styles[name].leading = 24
        styles[name].textColor = colors.black
        styles[name].spaceBefore = 12
        styles[name].spaceAfter = 0
        styles[name].keepWithNext = True
    styles.add(ParagraphStyle(name="CaptionP5", parent=styles["BodyP5"], fontSize=11, leading=16, firstLineIndent=0, spaceAfter=12))
    styles.add(ParagraphStyle(name="TableTitleP5", parent=styles["BodyP5"], fontName="Times-Bold", firstLineIndent=0, keepWithNext=True, spaceBefore=12))
    styles.add(ParagraphStyle(name="LabelP5", parent=styles["BodyP5"], firstLineIndent=0))
    styles.add(ParagraphStyle(name="TitlePageP5", parent=styles["BodyP5"], firstLineIndent=0, alignment=TA_CENTER))
    story = []
    text = (SOURCE / args.source).read_text()
    text += "\n\n[P5_APPENDIX]\n\n" + (SOURCE / "supplement.md").read_text()
    # [INCLUDE file.md] pulls in a generated table; [FIGURE file.png | caption] places a figure.
    text = re.sub(r"^\[INCLUDE ([^\]]+)\]$", lambda m: (SOURCE / m.group(1)).read_text(), text, flags=re.M)
    title_page = "[PAGEBREAK]" in text
    after_table = False
    for block in text.split("\n\n"):
        block = block.strip()
        if not block: continue
        note_follows_table, after_table = after_table, False
        if block == "[PAGEBREAK]":
            story.append(PageBreak())
            title_page = False
            continue
        if block == "[P5_APPENDIX]":
            story.append(PageBreak())
            continue
        if block.startswith("[FIGURE "):
            name, caption = [part.strip() for part in block[len("[FIGURE "):-1].split("|", 1)]
            width, height = ImageReader(str(SOURCE / name)).getSize()
            story.append(KeepTogether([Image(str(SOURCE / name), width=432, height=432 * height / width),
                                       Paragraph(escape(caption), styles["CaptionP5"]), Spacer(1, 8)]))
            continue
        if block.startswith("| "):
            data = []
            for line in block.splitlines():
                if set(line.replace("|", "").replace(":", "").replace(" ", "")) <= {"-"}: continue
                data.append([Paragraph(escape(v.strip()), styles["CellP5"]) for v in line.strip("|").split("|")])
            n = len(data[0])
            first = 468 * (0.42 if n <= 3 else 0.34 if n == 4 else 0.28)
            widths = [first] + [(468 - first) / (n - 1)] * (n - 1)
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("LINEABOVE", (0,0), (-1,0), .8, colors.black),
                ("VALIGN", (0,0), (-1,-1), "TOP"), ("LINEBELOW", (0,0), (-1,0), .6, colors.black), ("LINEBELOW", (0,-1), (-1,-1), .8, colors.black),
                
                ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
            heading = []
            if story and isinstance(story[-1], Paragraph) and story[-1].style.name in {"Heading1", "Heading2", "TableTitleP5"}:
                heading = [story.pop()]
            story += [KeepTogether([*heading, table, Spacer(1, 6)])]
            after_table = True
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
            style = (styles["TitlePageP5"] if title_page else styles["CaptionP5"] if note_follows_table
                     else styles["LabelP5"] if block.startswith("**") else styles["BodyP5"])
            story.append(Paragraph(fmt(block).replace("\n", " "), style))
    def footer(canvas, doc):
        canvas.setFont("Times-Roman", 9); canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(72, 36, args.footer)
        canvas.setFont("Times-Roman", 11); canvas.setFillColor(colors.black)
        canvas.drawRightString(540, 36, str(doc.page))
    SimpleDocTemplate(str(out), pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72,
                      bottomMargin=72, title="Autistic adults more often report absent sensory imagery", author="Ivan Habib").build(story, onFirstPage=footer, onLaterPages=footer)
    print(out)


if __name__ == "__main__":
    main()
