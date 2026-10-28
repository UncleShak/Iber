"""action-plan.pdf one-pager from the report model only (s0.8, s4.11).

Minimal version wired in by the CLI (phase 7); phase 9 owns the layout and
the one-page guarantee. Content: header (overall, summary, date), the five
category statuses, then top_fixes with title, why and steps.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

MARGIN = 50
LINE = 14


def render(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fixes = {f["id"]: f for f in report["fixes"]}
    c = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - MARGIN

    def line(text: str, font: str = "Helvetica", size: int = 10) -> None:
        nonlocal y
        c.setFont(font, size)
        c.drawString(MARGIN, y, text)
        y -= LINE

    line(f"Overall: {report['overall'].upper()}", "Helvetica-Bold", 16)
    line(report["summary"])
    line(f"Generated {report['generated_at']}")
    y -= LINE
    for cat in report["categories"]:
        line(f"{cat['title']}: {cat['status']}")
    y -= LINE
    for n, fix_id in enumerate(report["top_fixes"], start=1):
        fix = fixes[fix_id]
        line(f"{n}. {fix['title']}", "Helvetica-Bold", 11)
        line(fix["why"])
        for step in fix["steps"]:
            line(f"  - {step}")
        y -= LINE / 2
    c.showPage()
    c.save()
