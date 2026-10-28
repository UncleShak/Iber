"""action-plan.pdf one-pager from the report model only (s0.8, s4.11).

Canvas API only, every block at an absolute position from the s4.11 layout
table, so nothing can flow onto a second page. Text never wraps past its
block: every line is cut with an ellipsis at the box width. Helvetica only;
status symbols are drawn as shapes because the built-in fonts carry no
glyphs for the s4.10 Unicode symbols. Every drawn string goes through
pdf_text(), which swaps the step arrow for ">" and keeps the text inside
cp1252, the only characters Helvetica can show.

Standalone: python -m antigravity_engine.render.pdf report.json action-plan.pdf
"""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from antigravity_engine.parser import validate_schema
from antigravity_engine.render.html import BADGES, PRODUCT, RAG_COLOURS, human_date
from antigravity_engine.report_model import REPORT_SCHEMA

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
LEFT = MARGIN
RIGHT = PAGE_W - MARGIN
WIDTH = RIGHT - LEFT

FONT = "Helvetica"
BOLD = "Helvetica-Bold"
ELLIPSIS = "\u2026"
DOT = "\u00b7"
EM_DASH = "\u2014"

ARROW = "\u2192"
SUBTITLE = "Cyber Health Action Plan"
TITLE = f"{PRODUCT} {EM_DASH} {SUBTITLE}"
ORG_MAX = 40
SUMMARY_LINES = 2
MAX_STEPS = 4
MORE_STEPS = f"{ELLIPSIS}see full report"
NOTHING_URGENT = "Nothing urgent. Re-check monthly."
FOOTER_PRIVACY = (
    f"Generated locally {EM_DASH} nothing was uploaded. Guidance only, not a full audit."
)

# s4.11 layout table, mm from the top edge.
HEADER = (15, 40)
SUMMARY = (42, 55)
STRIP = (58, 75)
FIXES = (80, 255)
FIX_BOX = 55
STRIP_BOX = 33.6
LEADING = 12 / mm  # 12 pt line spacing, in mm
FIX_GAP = 5
FOOTER = (265, 282)

INK = HexColor("#1a1a1a")
MUTED = HexColor("#667085")
RULE = HexColor("#e4e7ec")


def y_mm(top: float) -> float:
    """Distance from the top edge in mm -> ReportLab y in points."""
    return PAGE_H - top * mm


def tone(status: str) -> tuple:
    """(ink, background) for a status, from the s4.3 tokens."""
    name = BADGES[status]["tone"]
    return HexColor(RAG_COLOURS[name]), HexColor(RAG_COLOURS[f"{name}-bg"])


def pdf_text(text: str) -> str:
    """Make text drawable in Helvetica: "->" arrows become ">", anything else
    outside cp1252 becomes "?" rather than an empty box (wording spec s4.1)."""
    text = text.replace(ARROW, ">")
    return text.encode("cp1252", errors="replace").decode("cp1252")


def fit(text: str, font: str, size: float, width: float) -> str:
    """Cut text with an ellipsis so it is no wider than width points."""
    if stringWidth(text, font, size) <= width:
        return text
    while text and stringWidth(text.rstrip() + ELLIPSIS, font, size) > width:
        text = text[:-1]
    return text.rstrip() + ELLIPSIS


def wrap(text: str, font: str, size: float, width: float, max_lines: int) -> list[str]:
    """Greedy word wrap into at most max_lines; the last line takes the rest and is cut."""
    words = text.split()
    lines: list[str] = []
    while words and len(lines) < max_lines - 1:
        line = words.pop(0)
        while words and stringWidth(f"{line} {words[0]}", font, size) <= width:
            line = f"{line} {words.pop(0)}"
        lines.append(fit(line, font, size, width))
    if words:
        lines.append(fit(" ".join(words), font, size, width))
    return lines


def truncate_org(org: str) -> str:
    return org if len(org) <= ORG_MAX else org[: ORG_MAX - 1].rstrip() + ELLIPSIS


def fix_meta(fix: dict) -> str:
    meta = f"~{fix['effort_minutes']} min"
    return f"{meta} {DOT} Needs admin" if fix["needs_admin"] else meta


def _text(c, x: float, y: float, text: str, font: str = FONT, size: float = 10,
          colour=INK, width: float | None = None) -> None:
    text = pdf_text(text)
    c.setFont(font, size)
    c.setFillColor(colour)
    c.drawString(x, y, fit(text, font, size, width) if width is not None else text)


def _symbol(c, status: str, x: float, y: float, size: float) -> None:
    """s4.10 symbol drawn as a shape, centred on (x, y): circle, triangle, tick, no-entry, cross."""
    ink, _ = tone(status)
    r = size / 2
    c.saveState()
    c.setFillColor(ink)
    c.setStrokeColor(ink)
    c.setLineWidth(max(size / 7, 0.8))
    c.setLineCap(1)
    if status == "red":
        c.circle(x, y, r * 0.85, stroke=0, fill=1)
    elif status == "amber":
        p = c.beginPath()
        p.moveTo(x - r, y - r * 0.85)
        p.lineTo(x + r, y - r * 0.85)
        p.lineTo(x, y + r * 0.9)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    elif status == "green":
        p = c.beginPath()
        p.moveTo(x - r * 0.8, y)
        p.lineTo(x - r * 0.2, y - r * 0.6)
        p.lineTo(x + r * 0.85, y + r * 0.7)
        c.drawPath(p, stroke=1, fill=0)
    elif status == "unavailable":
        c.circle(x, y, r * 0.8, stroke=1, fill=0)
        c.line(x - r * 0.56, y - r * 0.56, x + r * 0.56, y + r * 0.56)
    else:
        c.line(x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7)
        c.line(x - r * 0.7, y + r * 0.7, x + r * 0.7, y - r * 0.7)
    c.restoreState()


def _box(c, x: float, top: float, w: float, h: float, status: str, dashed: bool = False) -> None:
    """Filled, bordered box; top and h in mm, x and w in points."""
    ink, bg = tone(status)
    c.saveState()
    c.setFillColor(bg)
    c.setStrokeColor(ink)
    c.setLineWidth(1)
    if dashed:
        c.setDash(3, 2)
    c.roundRect(x, y_mm(top + h), w, h * mm, 2 * mm, stroke=1, fill=1)
    c.restoreState()


def _status_label(c, status: str, x: float, y: float, size: float, width: float) -> None:
    """Symbol + word, never colour alone."""
    ink, _ = tone(status)
    _symbol(c, status, x + size / 2, y + size * 0.35, size)
    _text(c, x + size * 1.4, y, BADGES[status]["word"], BOLD, size, ink, width - size * 1.4)


def _header(c, report: dict, org: str | None) -> None:
    top, bottom = HEADER
    badge_w, badge_h = 45 * mm, 14
    text_w = WIDTH - badge_w - 4 * mm
    _text(c, LEFT, y_mm(top + 6), PRODUCT, BOLD, 20, INK, text_w)
    _text(c, LEFT, y_mm(top + 12), SUBTITLE, FONT, 12, INK, text_w)
    line = human_date(report["generated_at"])
    if org:
        line = f"{truncate_org(pdf_text(org))} {DOT} {line}"
    _text(c, LEFT, y_mm(top + 18), line, FONT, 9, MUTED, text_w)

    overall = report["overall"]
    _box(c, RIGHT - badge_w, top + 2, badge_w, badge_h, overall)
    _status_label(c, overall, RIGHT - badge_w + 4 * mm, y_mm(top + 2 + badge_h / 2 + 1.5),
                  12, badge_w - 8 * mm)

    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(LEFT, y_mm(bottom), RIGHT, y_mm(bottom))


def _summary(c, report: dict) -> None:
    top, _ = SUMMARY
    lines = wrap(pdf_text(report["summary"]), FONT, 11, WIDTH, SUMMARY_LINES)
    for n, line in enumerate(lines):
        _text(c, LEFT, y_mm(top + 4.5 + n * 5), line, FONT, 11)


def _strip(c, report: dict) -> None:
    top, bottom = STRIP
    gap = 3 * mm
    w = STRIP_BOX * mm
    inner = w - 5 * mm
    for n, cat in enumerate(report["categories"]):
        x = LEFT + n * (w + gap)
        _box(c, x, top, w, bottom - top, cat["status"], dashed=cat["status"] == "failed")
        for i, line in enumerate(wrap(pdf_text(cat["title"]), BOLD, 8, inner, 2)):
            _text(c, x + 2.5 * mm, y_mm(top + 4.5 + i * 3.4), line, BOLD, 8)
        _status_label(c, cat["status"], x + 2.5 * mm, y_mm(bottom - 3), 9, inner)


def _fix(c, rank: int, fix: dict, top: float) -> None:
    severity = fix["severity"]
    ink, _ = tone(severity)
    x = LEFT
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(1)
    c.rect(x, y_mm(top + FIX_BOX), WIDTH, FIX_BOX * mm, stroke=1, fill=0)
    c.setFillColor(ink)
    c.rect(x, y_mm(top + FIX_BOX), 2 * mm, FIX_BOX * mm, stroke=0, fill=1)
    # rank in a filled circle, 8 mm across
    cx, cy = x + 9 * mm, y_mm(top + 7)
    c.circle(cx, cy, 4 * mm, stroke=0, fill=1)
    c.restoreState()
    c.setFont(BOLD, 12)
    c.setFillColor(HexColor("#ffffff"))
    c.drawCentredString(cx, cy - 4.2, str(rank))

    # severity word top right, so severity is never colour alone
    word = BADGES[severity]["word"]
    word_w = stringWidth(word, BOLD, 9)
    _text(c, RIGHT - 4 * mm - word_w, y_mm(top + 6), word, BOLD, 9, ink)

    tx = x + 16 * mm
    tw = RIGHT - 4 * mm - tx
    _text(c, tx, y_mm(top + 8.5), fix["title"], BOLD, 13, INK, tw - word_w - 4 * mm)
    y = top + 15
    for line in wrap(pdf_text(fix["why"]), FONT, 10, tw, 2):
        _text(c, tx, y_mm(y), line, FONT, 10)
        y += LEADING
    y += 1.5
    steps = fix["steps"]
    shown = steps if len(steps) <= MAX_STEPS else steps[: MAX_STEPS - 1]
    for n, step in enumerate(shown, start=1):
        _text(c, tx, y_mm(y), f"{n}. {step}", FONT, 10, INK, tw)
        y += LEADING
    if len(steps) > MAX_STEPS:
        _text(c, tx, y_mm(y), MORE_STEPS, FONT, 10, MUTED, tw)
    _text(c, tx, y_mm(top + FIX_BOX - 4), fix_meta(fix), FONT, 9, MUTED, tw)


def _fixes(c, report: dict) -> None:
    top, bottom = FIXES
    fixes = {f["id"]: f for f in report["fixes"]}
    top_fixes = report["top_fixes"][:3]
    if not top_fixes:
        green = tone("green")[0]
        text_w = stringWidth(NOTHING_URGENT, FONT, 13)
        tick = 5 * mm
        start = LEFT + (WIDTH - text_w - tick - 3 * mm) / 2
        y = y_mm((top + bottom) / 2)
        _symbol(c, "green", start + tick / 2, y + 13 * 0.35, 13)
        _text(c, start + tick + 3 * mm, y, NOTHING_URGENT, FONT, 13, green)
        return
    for n, fix_id in enumerate(top_fixes, start=1):
        _fix(c, n, fixes[fix_id], top + (n - 1) * (FIX_BOX + FIX_GAP))


def _footer(c, report: dict, evidence_id: str | None) -> None:
    top, _ = FOOTER
    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(LEFT, y_mm(top), RIGHT, y_mm(top))
    _text(c, LEFT, y_mm(top + 5), FOOTER_PRIVACY, FONT, 8, MUTED, WIDTH)
    versions = (
        f"Engine {report['engine_version']} {DOT} Baseline {report['baseline_version']}"
        f" {DOT} {report['scan']['os_caption']}"
    )
    if evidence_id:
        versions += f" {DOT} Evidence ID {evidence_id}"
    _text(c, LEFT, y_mm(top + 9.5), versions, FONT, 7.5, MUTED, WIDTH)


def render(
    report: dict, path: Path, org: str | None = None, evidence_id: str | None = None
) -> int:
    """Draw the one-pager; returns the number of pages drawn (always 1).

    org is the licence organisation, known only to the app (D16); omitted if None.
    evidence_id ("AG-...", s2.14.1) goes in the footer; omitted if None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # invariant: fixed creation date and document id, so the same report gives the same bytes.
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    c.setTitle(TITLE)
    c.setAuthor(PRODUCT)
    _header(c, report, org)
    _summary(c, report)
    _strip(c, report)
    _fixes(c, report)
    _footer(c, report, evidence_id)
    c.showPage()
    pages = c.getPageNumber() - 1
    c.save()
    return pages


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m antigravity_engine.render.pdf REPORT_JSON OUT_PDF",
              file=sys.stderr)
        return 2
    report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    validate_schema(report, REPORT_SCHEMA)
    render(report, Path(args[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
