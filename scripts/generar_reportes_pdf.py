from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

RAIZ = Path(__file__).resolve().parents[1]


def markdown_a_pdf(origen, destino, titulo):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleReport", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="H1Report", parent=styles["Heading1"], spaceBefore=10, spaceAfter=8))
    styles.add(ParagraphStyle(name="H2Report", parent=styles["Heading2"], spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="BodyReport", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=5))
    doc = SimpleDocTemplate(str(destino), pagesize=letter, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42, title=titulo)
    story = []
    for raw in origen.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        text = text.replace("&", "&amp;").replace("→", "->").replace("—", "-").replace("×", "x").replace("≥", ">=")
        if text.startswith("# "):
            story.append(Paragraph(text[2:], styles["TitleReport"]))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], styles["H1Report"]))
        elif text.startswith("### "):
            story.append(Paragraph(text[4:], styles["H2Report"]))
        elif text.startswith("- "):
            story.append(Paragraph("• " + text[2:], styles["BodyReport"]))
        elif text.startswith("> "):
            story.append(Paragraph("<i>" + text[2:] + "</i>", styles["BodyReport"]))
        else:
            if text.startswith("---"):
                story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(text, styles["BodyReport"]))
    doc.build(story)


def main():
    markdown_a_pdf(RAIZ / "docs" / "AUDITORIA.md", RAIZ / "docs" / "AUDITORIA.pdf", "Diagnóstico de auditoría integral")
    markdown_a_pdf(RAIZ / "docs" / "reporte-final.md", RAIZ / "docs" / "reporte-final.pdf", "Reporte técnico final")
    print(RAIZ / "docs" / "AUDITORIA.pdf")
    print(RAIZ / "docs" / "reporte-final.pdf")


if __name__ == "__main__":
    main()
