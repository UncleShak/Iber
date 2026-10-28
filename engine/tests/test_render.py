"""report.html (phase 8, s4.10) and action-plan.pdf (phase 9, s4.11)."""

import copy
import json
import re
from pathlib import Path

import pytest

from antigravity_engine.__main__ import assess
from markupsafe import escape

from antigravity_engine.parser import ContractError, parse_path
from antigravity_engine.render import html, pdf
from conftest import FIXTURES

SCAN_FIXTURES = sorted(FIXTURES.glob("scan.*.json"))
XSS = FIXTURES / "scan.xss.json"
FOOTER_LOCAL = "Generated locally on this PC. Nothing was uploaded."
FOOTER_AUDIT = "This is a guidance check, not a full security audit."
ALL_NULL_RECOVERY = {
    "host": {"is_admin": False},
    "recovery": {
        "winre_enabled": None,
        "system_restore_enabled": None,
        "restore_point_count": None,
        "latest_restore_point": None,
    },
}


def _report(path, baseline) -> dict:
    return assess(parse_path(path), baseline)


def _section(page: str, category_id: str) -> str:
    start = page.index(f'<section class="category" id="{category_id}">')
    return page[start : page.index("</section>", start)]


def html_escape(text: str) -> str:
    return str(escape(text))


def _rows(section: str) -> list[str]:
    """Body rows only; the header row holds <th> cells."""
    return [r for r in re.findall(r"<tr>.*?</tr>", section, flags=re.S) if "<td" in r]


@pytest.fixture
def defender_off(baseline) -> dict:
    return _report(FIXTURES / "scan.defender-off.json", baseline)


# --- every fixture renders ---


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_every_fixture_renders(path, baseline, tmp_path):
    report = _report(path, baseline)
    out = tmp_path / "report.html"
    html.render(report, out)
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    assert page.rstrip().endswith("</html>")
    for c in report["categories"]:
        assert f'id="{c["id"]}"' in page


# --- self-contained (s4.10 row 1) ---


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_page_is_self_contained(path, baseline):
    page = html.render_string(_report(path, baseline)).lower()
    assert "<script" not in page
    for external in ("http://", "https://", "//cdn", "<link", "<img", "@import", "url(", "@font-face"):
        assert external not in page, external
    assert page.count("<style>") == 1


# --- autoescape (s4.10 row 2) ---


def test_environment_autoescapes():
    assert html._env().autoescape is True


def test_xss_fixture_renders_without_raw_script(baseline):
    page = html.render_string(_report(XSS, baseline))
    assert "<script>alert" not in page
    assert "<img" not in page


def test_xss_app_name_is_escaped_wherever_the_report_carries_it(baseline):
    # Put the fixture's own payload into every scan-driven text field, including
    # ones the xss scan itself cannot reach, to prove escaping everywhere.
    name = json.loads(XSS.read_text(encoding="utf-8"))["host"]["os_caption"]
    report = copy.deepcopy(_report(FIXTURES / "scan.defender-off.json", baseline))
    software = next(c for c in report["categories"] if c["id"] == "software")
    software["evidence"][0]["label"] = name
    software["evidence"][0]["value"] = name
    report["fixes"][0]["steps"][0] = f"Update {name}"
    report["summary"] = name

    page = html.render_string(report, org=name)
    assert "<script>alert" not in page
    assert "<img src=x" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    # summary, org, evidence label and value, and the step in both the top
    # fixes and the category's own fix block
    assert page.count("&lt;script&gt;alert(1)") == 6


# --- RAG tokens and badges (s4.3, s4.9.3) ---


def test_exact_s4_3_hex_values():
    assert html.RAG_COLOURS == {
        "red": "#b42318", "red-bg": "#fef3f2",
        "amber": "#b54708", "amber-bg": "#fffaeb",
        "green": "#067647", "green-bg": "#ecfdf3",
        "grey": "#475467", "grey-bg": "#f2f4f7",
    }


def test_page_uses_only_token_hexes_for_rag(defender_off):
    page = html.render_string(defender_off)
    for name, hex_value in html.RAG_COLOURS.items():
        assert f"--{name}: {hex_value};" in page


@pytest.mark.parametrize(
    "status, symbol, word",
    [
        ("red", "\u25cf", "Act now"),
        ("amber", "\u25b2", "Improve"),
        ("green", "\u2713", "Good"),
        ("unavailable", "\u2298", "Not checked"),
        ("failed", "\u2715", "Check failed"),
    ],
)
def test_badge_has_symbol_and_word(status, symbol, word):
    assert html.badge(status)["symbol"] == symbol
    assert html.badge(status)["word"] == word


def test_overall_badge_shows_symbol_word_and_colour(defender_off):
    page = html.render_string(defender_off)
    header = page[page.index("<header>") : page.index("</header>")]
    assert 'class="badge badge-red badge-lg"' in header
    assert "\u25cf</span> Act now" in header


def test_failed_badge_is_dashed(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][4].update(status="failed", evidence=[], fix_ids=[])
    page = html.render_string(report)
    assert "badge badge-grey badge-failed" in _section(page, "recovery")


# --- section order (s4.10 structure) ---


def test_sections_in_fixed_order(defender_off):
    page = html.render_string(defender_off)
    marks = [
        "<header>",
        '<section id="actions">',
        '<section id="overview">',
        *[f'<section class="category" id="{c}">' for c in
          ("backup", "patch", "software", "protection", "recovery")],
        "<footer>",
    ]
    positions = [page.index(m) for m in marks]
    assert positions == sorted(positions)


def test_header_has_product_summary_and_date(defender_off):
    page = html.render_string(defender_off)
    header = page[page.index("<header>") : page.index("</header>")]
    assert "Antigravity" in header
    assert html_escape(defender_off["summary"]) in header
    assert f"Checked on {html.human_date(defender_off['generated_at'])}" in header


def test_licence_org_only_when_given(defender_off):
    assert "Licensed to" not in html.render_string(defender_off)
    assert "Licensed to Acme Bakery" in html.render_string(defender_off, org="Acme Bakery")


def test_top_fixes_numbered_in_report_order(defender_off):
    page = html.render_string(defender_off)
    actions = page[page.index('<section id="actions">') : page.index('<section id="overview">')]
    expected = [f["title"] for fid in defender_off["top_fixes"]
                for f in defender_off["fixes"] if f["id"] == fid]
    found = re.findall(
        r'<span class="rank" aria-hidden="true">(\d)</span>\s*<div class="fix-body">\s*'
        r'<h3><span class="sr">Fix \d: </span>(.*?) <span', actions)
    assert [int(n) for n, _ in found] == list(range(1, len(expected) + 1))
    assert [t for _, t in found] == [html_escape(t) for t in expected]


def test_no_top_fixes_says_nothing_urgent(baseline):
    page = html.render_string(_report(FIXTURES / "scan.healthy.json", baseline))
    assert "Nothing urgent. Re-check monthly." in page
    assert 'class="top"' not in page


def test_strip_has_five_anchor_tiles(defender_off):
    page = html.render_string(defender_off)
    for c in defender_off["categories"]:
        assert f'<a class="tile" href="#{c["id"]}">' in page
    assert page.count('class="tile"') == 5


def test_each_category_lists_its_fixes_with_why_and_steps(defender_off):
    page = html.render_string(defender_off)
    fixes = {f["id"]: f for f in defender_off["fixes"]}
    for c in defender_off["categories"]:
        section = _section(page, c["id"])
        for fix_id in c["fix_ids"]:
            assert f'id="fix-{fix_id}"' in section
            assert html_escape(fixes[fix_id]["why"]) in section
            for step in fixes[fix_id]["steps"]:
                assert f"<li>{html_escape(step)}</li>" in section


def test_footer_lines_and_versions(defender_off):
    page = html.render_string(defender_off)
    footer = page[page.index("<footer>") :]
    assert FOOTER_LOCAL in footer
    assert FOOTER_AUDIT in footer
    assert f"Engine {defender_off['engine_version']}" in footer
    assert f"Baseline {defender_off['baseline_version']}" in footer


# --- evidence rows (s4.10 evidence table) ---


def test_unavailable_category_row_says_not_checked_never_check_failed(make_scan, baseline):
    report = assess(make_scan(ALL_NULL_RECOVERY), baseline)
    recovery = next(c for c in report["categories"] if c["id"] == "recovery")
    assert recovery["status"] == "unavailable"

    section = _section(html.render_string(report), "recovery")
    rows = _rows(section)
    assert len(rows) == len(recovery["evidence"]) == 4
    for row in rows:
        assert "Not checked" in row
        assert "Check failed" not in row
        assert 'class="grey"' in row
    assert "Check failed" not in section


def test_unavailable_value_gets_not_checked_prefix():
    row = {"label": "BitLocker", "value": "Not available on Windows Home", "status": "unavailable"}
    assert html.evidence_value(row) == "Not checked \u2014 not available on Windows Home"


def test_unavailable_value_already_prefixed_is_kept():
    row = {"label": "BitLocker", "value": "Not checked \u2014 needs admin", "status": "unavailable"}
    assert html.evidence_value(row) == "Not checked \u2014 needs admin"


def test_failed_value_gets_couldnt_read_prefix(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][3]["evidence"][0].update(value="Cmdlet threw", status="failed")
    row = _rows(_section(html.render_string(report), "protection"))[0]
    assert '<td class="grey">Couldn&#39;t read: Cmdlet threw</td>' in row
    assert '\u2715</span><span class="sr"> Check failed</span>' in row
    assert "Not checked" not in row


def test_rated_row_shows_coloured_symbol_and_normal_text(defender_off):
    rows = _rows(_section(html.render_string(defender_off), "protection"))
    red = [r for r in rows if "state-red" in r]
    assert red
    for r in red:
        assert '\u25cf</span><span class="sr"> Act now</span>' in r
        assert 'class="grey"' not in r


def test_row_without_status_is_neutral(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][0]["evidence"] = [{"label": "Note", "value": "Plain fact"}]
    row = _rows(_section(html.render_string(report), "backup"))[0]
    assert '<td class="state"></td>' in row
    for b in html.BADGES.values():
        assert b["symbol"] not in row
    assert 'class="grey"' not in row


# --- print and width (s4.10 rows 5, 6) ---


def test_print_rules_and_max_width(defender_off):
    page = html.render_string(defender_off)
    style = page[page.index("<style>") : page.index("</style>")]
    assert "max-width: 860px;" in style
    printing = style[style.index("@media print") :]
    assert "size: A4;" in printing
    assert "background: none !important;" in printing
    assert "page-break-inside: avoid;" in printing
    assert ".category" in printing


def test_human_date():
    assert html.human_date("2026-11-04T17:02:46Z") == "4 Nov 2026"


# --- standalone entry point ---


def test_main_renders_report_json(defender_off, tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps(defender_off), encoding="utf-8")
    out = tmp_path / "out" / "report.html"
    assert html.main([str(src), str(out)]) == 0
    assert FOOTER_LOCAL in out.read_text(encoding="utf-8")


def test_main_rejects_invalid_report(tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps({"overall": "red"}), encoding="utf-8")
    with pytest.raises(ContractError):
        html.main([str(src), str(tmp_path / "report.html")])


def test_main_usage(capsys):
    assert html.main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_renderer_never_reads_the_scan():
    # s2.3 row 9: render from the report model only.
    source = (html.TEMPLATES.parent / "render" / "html.py").read_text(encoding="ascii")
    assert "parse_path" not in source and "ScanModel" not in source


# --- action-plan.pdf (s4.11, phase 9) ---


def _pdf_page_count(path) -> int:
    """Page objects in the file; "/Type /Pages" is the tree root, not a page."""
    return len(re.findall(rb"/Type /Page(?![a-zA-Z])", path.read_bytes()))


def _all_green(report: dict) -> dict:
    out = copy.deepcopy(report)
    out["overall"] = "green"
    for c in out["categories"]:
        c["status"] = "green"
        c["fix_ids"] = []
    out["fixes"] = []
    out["top_fixes"] = []
    return out


def _stress(report: dict) -> dict:
    """Every status in the strip and fixes far longer than any box."""
    out = copy.deepcopy(report)
    for c, status in zip(out["categories"], ["red", "amber", "green", "unavailable", "failed"]):
        c["status"] = status
        c["title"] = "A category title much too long for one strip box " * 2
    out["summary"] = "This summary sentence keeps going far past two lines of text. " * 8
    for f in out["fixes"]:
        f["title"] = "W" * 200
        f["why"] = "A reason that wraps and wraps. " * 20
        f["steps"] = [f"Step with very long text {'x' * 150}"] * 9
    return out


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_pdf_is_one_page_for_every_fixture(path, baseline, tmp_path):
    out = tmp_path / "action-plan.pdf"
    assert pdf.render(_report(path, baseline), out) == 1
    assert out.read_bytes().startswith(b"%PDF")
    assert _pdf_page_count(out) == 1


def test_pdf_all_green_is_one_page(defender_off, tmp_path):
    out = tmp_path / "action-plan.pdf"
    assert pdf.render(_all_green(defender_off), out) == 1
    assert out.read_bytes().startswith(b"%PDF")
    assert _pdf_page_count(out) == 1


def test_pdf_overflowing_report_is_still_one_page(defender_off, tmp_path):
    out = tmp_path / "action-plan.pdf"
    org = "An Organisation Name Far Longer Than Forty Characters (Pty) Ltd"
    assert pdf.render(_stress(defender_off), out, org=org) == 1
    assert _pdf_page_count(out) == 1


def test_pdf_xss_fixture_does_not_raise(baseline, tmp_path):
    out = tmp_path / "action-plan.pdf"
    assert pdf.render(_report(XSS, baseline), out) == 1


def test_pdf_non_latin_text_does_not_raise(defender_off, tmp_path):
    report = copy.deepcopy(defender_off)
    report["fixes"][0]["title"] = "\u4e2d\u6587 \U0001F600 <script>alert(1)</script>"
    assert pdf.render(report, tmp_path / "action-plan.pdf", org="\u00c9cole \u4e2d") == 1


def test_pdf_render_draws_one_show_page(defender_off, tmp_path, monkeypatch):
    # s4.11 test: the canvas reports exactly one showPage() call.
    calls = []
    real = pdf.canvas.Canvas.showPage
    monkeypatch.setattr(pdf.canvas.Canvas, "showPage",
                        lambda self: (calls.append(1), real(self))[1])
    pdf.render(defender_off, tmp_path / "action-plan.pdf")
    assert calls == [1]


def test_pdf_is_deterministic(defender_off, tmp_path):
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    pdf.render(defender_off, a)
    pdf.render(defender_off, b)
    assert a.read_bytes() == b.read_bytes()


def test_pdf_layout_matches_s4_11_table():
    assert pdf.PAGE_W == pytest.approx(210 * pdf.mm)
    assert pdf.PAGE_H == pytest.approx(297 * pdf.mm)
    assert pdf.MARGIN == pytest.approx(15 * pdf.mm)
    assert (pdf.HEADER, pdf.SUMMARY, pdf.STRIP, pdf.FIXES, pdf.FOOTER) == (
        (15, 40), (42, 55), (58, 75), (80, 255), (265, 282))
    # three fix boxes fill 80-255 mm exactly
    assert pdf.FIXES[0] + 3 * pdf.FIX_BOX + 2 * pdf.FIX_GAP == pdf.FIXES[1]


def test_pdf_uses_s4_3_colours():
    for status in ("red", "amber", "green"):
        ink, bg = pdf.tone(status)
        assert ink.hexval() == "0x" + html.RAG_COLOURS[status][1:]
        assert bg.hexval() == "0x" + html.RAG_COLOURS[f"{status}-bg"][1:]
    for status in ("unavailable", "failed"):
        assert pdf.tone(status)[0].hexval() == "0x" + html.RAG_COLOURS["grey"][1:]


def test_pdf_uses_helvetica_only(defender_off, tmp_path):
    out = tmp_path / "action-plan.pdf"
    pdf.render(defender_off, out)
    fonts = set(re.findall(rb"/BaseFont /([A-Za-z-]+)", out.read_bytes()))
    assert fonts == {b"Helvetica", b"Helvetica-Bold"}
    assert b"/FontFile" not in out.read_bytes()


def test_fit_leaves_short_text_alone():
    assert pdf.fit("Short", pdf.FONT, 10, 200) == "Short"


def test_fit_cuts_with_ellipsis_at_box_width():
    width = 100
    cut = pdf.fit("x" * 200, pdf.FONT, 10, width)
    assert cut.endswith(pdf.ELLIPSIS)
    assert pdf.stringWidth(cut, pdf.FONT, 10) <= width
    assert pdf.stringWidth(cut + "x", pdf.FONT, 10) > width


def test_wrap_respects_max_lines_and_width():
    width = 150
    lines = pdf.wrap("word " * 100, pdf.FONT, 12, width, 2)
    assert len(lines) == 2
    assert lines[-1].endswith(pdf.ELLIPSIS)
    assert all(pdf.stringWidth(line, pdf.FONT, 12) <= width for line in lines)


def test_wrap_short_text_is_one_line():
    assert pdf.wrap("2 urgent issues.", pdf.FONT, 12, 400, 2) == ["2 urgent issues."]


def test_org_truncated_to_40_chars():
    assert pdf.truncate_org("A" * 40) == "A" * 40
    cut = pdf.truncate_org("B" * 41)
    assert len(cut) == 40 and cut.endswith(pdf.ELLIPSIS)


def test_fix_meta_says_needs_admin_only_when_true():
    assert pdf.fix_meta({"effort_minutes": 5, "needs_admin": True}) == "~5 min \u00b7 Needs admin"
    assert pdf.fix_meta({"effort_minutes": 20, "needs_admin": False}) == "~20 min"


def test_pdf_wording_matches_s4_11():
    assert pdf.TITLE == "Antigravity \u2014 Cyber Health Action Plan"
    assert pdf.NOTHING_URGENT == "Nothing urgent. Re-check monthly."
    assert pdf.MORE_STEPS == "\u2026see full report"
    assert pdf.MAX_STEPS == 4
    assert pdf.FOOTER_PRIVACY == (
        "Generated locally \u2014 nothing was uploaded. Guidance only, not a full audit.")


def _drawn_strings(report, tmp_path, monkeypatch) -> list[str]:
    drawn = []
    real = pdf.canvas.Canvas.drawString
    monkeypatch.setattr(pdf.canvas.Canvas, "drawString",
                        lambda self, x, y, text, *a, **k: (drawn.append(text),
                                                           real(self, x, y, text, *a, **k))[1])
    pdf.render(report, tmp_path / "action-plan.pdf")
    return drawn


def test_pdf_shows_four_steps_then_see_full_report(defender_off, tmp_path, monkeypatch):
    report = copy.deepcopy(defender_off)
    fix = next(f for f in report["fixes"] if f["id"] == report["top_fixes"][0])
    fix["steps"] = [f"Step {n}" for n in range(1, 7)]
    drawn = _drawn_strings(report, tmp_path, monkeypatch)
    # wording spec s4.3: more than 4 steps -> the fourth line becomes the pointer
    assert [s for s in drawn if s.startswith(("1. Step", "3. Step"))] == ["1. Step 1", "3. Step 3"]
    assert "4. Step 4" not in drawn
    assert pdf.MORE_STEPS in drawn


def test_pdf_shows_exactly_four_steps_without_pointer(defender_off, tmp_path, monkeypatch):
    report = copy.deepcopy(defender_off)
    for f in report["fixes"]:
        f["steps"] = [f"Step {n}" for n in range(1, 5)]
    drawn = _drawn_strings(report, tmp_path, monkeypatch)
    assert "4. Step 4" in drawn
    assert pdf.MORE_STEPS not in drawn


def test_pdf_draws_top_fixes_in_report_order(defender_off, tmp_path, monkeypatch):
    ranks = []
    real = pdf.canvas.Canvas.drawCentredString
    monkeypatch.setattr(pdf.canvas.Canvas, "drawCentredString",
                        lambda self, x, y, text, *a, **k: (ranks.append(text),
                                                           real(self, x, y, text, *a, **k))[1])
    drawn = _drawn_strings(defender_off, tmp_path, monkeypatch)
    titles = {f["id"]: f["title"] for f in defender_off["fixes"]}
    expected = [titles[i] for i in defender_off["top_fixes"]]
    assert [s for s in drawn if s in expected] == expected
    assert ranks == ["1", "2", "3"][: len(expected)]


def test_pdf_zero_fixes_says_nothing_urgent(defender_off, tmp_path, monkeypatch):
    drawn = _drawn_strings(_all_green(defender_off), tmp_path, monkeypatch)
    assert pdf.NOTHING_URGENT in drawn


def test_pdf_strip_has_word_for_every_category(defender_off, tmp_path, monkeypatch):
    drawn = _drawn_strings(defender_off, tmp_path, monkeypatch)
    fixes = {f["id"]: f for f in defender_off["fixes"]}
    words = [html.BADGES[c["status"]]["word"] for c in defender_off["categories"]]
    overall = html.BADGES[defender_off["overall"]]["word"]
    # each fix box also names its severity, so it is never colour alone
    severities = [html.BADGES[fixes[i]["severity"]]["word"] for i in defender_off["top_fixes"][:3]]
    for word in set(words):
        assert drawn.count(word) == words.count(word) + (word == overall) + severities.count(word)


def test_pdf_footer_has_privacy_line_and_versions(defender_off, tmp_path, monkeypatch):
    drawn = _drawn_strings(defender_off, tmp_path, monkeypatch)
    assert pdf.FOOTER_PRIVACY in drawn
    versions = next(s for s in drawn if s.startswith("Engine "))
    assert defender_off["engine_version"] in versions
    assert defender_off["baseline_version"] in versions


def test_pdf_every_drawn_line_fits_the_page(defender_off, tmp_path, monkeypatch):
    drawn = []
    real = pdf.canvas.Canvas.drawString

    def spy(self, x, y, text, *a, **k):
        drawn.append((x, y, self.stringWidth(text, self._fontname, self._fontsize)))
        return real(self, x, y, text, *a, **k)

    monkeypatch.setattr(pdf.canvas.Canvas, "drawString", spy)
    pdf.render(_stress(defender_off), tmp_path / "action-plan.pdf",
               org="Org " * 30)
    for x, y, w in drawn:
        assert pdf.LEFT <= x and x + w <= pdf.RIGHT + 0.01
        assert pdf.y_mm(pdf.FOOTER[1]) <= y <= pdf.y_mm(pdf.HEADER[0])


def test_pdf_main_renders_report_json(defender_off, tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps(defender_off), encoding="utf-8")
    out = tmp_path / "action-plan.pdf"
    assert pdf.main([str(src), str(out)]) == 0
    assert out.read_bytes().startswith(b"%PDF")


def test_pdf_main_usage(capsys):
    assert pdf.main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_pdf_renderer_never_reads_the_scan():
    source = Path(pdf.__file__).read_text(encoding="ascii")
    assert "parse_path" not in source and "ScanModel" not in source


# --- report design and wording spec (Brick C, C7) ---


def _all_states(report: dict) -> dict:
    """One category per status, plus a failed and an unavailable evidence row."""
    out = copy.deepcopy(report)
    statuses = ["red", "amber", "green", "unavailable", "failed"]
    for c, status in zip(out["categories"], statuses):
        c["status"] = status
    out["categories"][3]["evidence"].append(
        {"label": "BitLocker", "value": "Not checked \u2014 needs admin", "status": "unavailable"})
    out["categories"][4]["evidence"] = [
        {"label": "System Restore", "value": "Cmdlet threw", "status": "failed"}]
    out["scan"]["is_admin"] = False
    return out


def _actions(page: str) -> str:
    return page[page.index('<section id="actions">') : page.index('<section id="overview">')]


def test_html_title_and_one_h1(defender_off):
    page = html.render_string(defender_off)
    date = html.human_date(defender_off["generated_at"])
    assert f"<title>Antigravity &mdash; Cyber Health Check &mdash; {date}</title>" in page
    assert page.count("<h1") == 1
    assert "<h1><strong>Antigravity</strong> Cyber Health Check</h1>" in page


def test_html_uses_spec_font_stack(defender_off):
    assert 'font-family: "Segoe UI", system-ui, Arial, sans-serif;' in html.render_string(defender_off)


def test_all_states_shows_every_status_word(defender_off):
    page = html.render_string(_all_states(defender_off))
    for b in html.BADGES.values():
        assert f"{b['symbol']}</span> {b['word']}" in page, b["word"]


@pytest.mark.parametrize("count, heading", [
    (3, "Your top 3 fixes"), (2, "Your top 2 fixes"), (1, "Your top fix")])
def test_top_fixes_heading_follows_count(defender_off, count, heading):
    report = copy.deepcopy(defender_off)
    report["top_fixes"] = report["top_fixes"][:count]
    assert f"<h2>{heading}</h2>" in _actions(html.render_string(report))


def test_top_fixes_capped_at_three(defender_off):
    report = copy.deepcopy(defender_off)
    report["top_fixes"] = [f["id"] for f in report["fixes"]]
    assert len(report["top_fixes"]) > 3
    actions = _actions(html.render_string(report))
    assert actions.count('class="rank"') == 3
    assert "Your top 3 fixes" in actions


def test_top_fix_shows_steps_and_meta(defender_off):
    actions = _actions(html.render_string(defender_off))
    first = next(f for f in defender_off["fixes"] if f["id"] == defender_off["top_fixes"][0])
    assert '<p class="steps-label">Steps</p>' in actions
    for step in first["steps"]:
        assert f"<li>{html_escape(step)}</li>" in actions
    meta = f"~{first['effort_minutes']} min"
    if first["needs_admin"]:
        meta += " &middot; Needs admin"
    assert f'<p class="meta">{meta}</p>' in actions


def test_category_fix_tagged_with_top_rank(defender_off):
    page = html.render_string(defender_off)
    fixes = {f["id"]: f for f in defender_off["fixes"]}
    for n, fix_id in enumerate(defender_off["top_fixes"], start=1):
        section = _section(page, fixes[fix_id]["category"])
        assert f'<span class="tag">Top fix {n}</span>' in section


def test_category_without_fixes_says_nothing_to_fix(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][2]["fix_ids"] = []
    assert "Nothing to fix here." in _section(html.render_string(report), "software")


def test_unavailable_hint_only_when_not_admin(defender_off):
    hint = "Run Antigravity as administrator for a full check."
    report = _all_states(defender_off)
    assert hint in _section(html.render_string(report), "protection")
    report["scan"]["is_admin"] = True
    page = html.render_string(report)
    assert hint not in page
    assert "Scanned without admin rights" not in page


def test_non_admin_note_wording(defender_off):
    report = copy.deepcopy(defender_off)
    report["scan"]["is_admin"] = False
    header = html.render_string(report).split("</header>")[0]
    assert "Scanned without admin rights, so some checks were skipped.</p>" in header


def test_evidence_headers_and_screen_reader_word(defender_off):
    section = _section(html.render_string(defender_off), "protection")
    assert ('<th scope="col">What we looked at</th><th scope="col">What we found</th>'
            '<th scope="col">Status</th>') in section


def test_overview_heading(defender_off):
    assert "<h2>The 5 checks at a glance</h2>" in html.render_string(defender_off)


def test_footer_versions_line_has_os(defender_off):
    footer = html.render_string(defender_off).split("<footer>")[1]
    assert (f"Engine {defender_off['engine_version']} &middot; Baseline "
            f"{defender_off['baseline_version']} &middot; "
            f"{html_escape(defender_off['scan']['os_caption'])}") in footer


def test_human_date_is_local(monkeypatch):
    import time
    monkeypatch.setenv("TZ", "Pacific/Auckland")
    time.tzset()
    try:
        assert html.human_date("2026-11-14T22:30:00Z") == "15 Nov 2026"
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()


def _report_strings(report: dict) -> list[str]:
    out = [report["summary"], report["scan"]["os_caption"]]
    for c in report["categories"]:
        out.append(c["title"])
    for f in report["fixes"]:
        out += [f["title"], f["why"], *f["steps"]]
    return out


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_pdf_fixture_text_is_cp1252_after_arrow_swap(path, baseline):
    # wording spec s4.1: only the arrow may be changed; anything else lost is a bug
    for text in _report_strings(_report(path, baseline)):
        if path != XSS:
            text.replace(pdf.ARROW, ">").encode("cp1252")
        assert pdf.pdf_text(text).encode("cp1252")


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_pdf_every_drawn_string_encodes_cp1252(path, baseline, tmp_path, monkeypatch):
    drawn = _drawn_strings(_report(path, baseline), tmp_path, monkeypatch)
    for text in drawn:
        text.encode("cp1252")


def test_pdf_arrow_becomes_greater_than():
    assert pdf.pdf_text("Open Start \u2192 Windows Security") == "Open Start > Windows Security"


def test_pdf_long_org_truncated_in_header(defender_off, tmp_path, monkeypatch):
    org = "An Organisation Name Far Longer Than Forty Characters (Pty) Ltd"
    drawn = []
    real = pdf.canvas.Canvas.drawString
    monkeypatch.setattr(pdf.canvas.Canvas, "drawString",
                        lambda self, x, y, text, *a, **k: (drawn.append(text),
                                                           real(self, x, y, text, *a, **k))[1])
    pdf.render(defender_off, tmp_path / "a.pdf", org=org)
    line = next(s for s in drawn if s.startswith("An Organisation"))
    assert line.startswith(pdf.truncate_org(org) + " ")
    assert pdf.ELLIPSIS in line


def test_pdf_header_and_footer_wording(defender_off, tmp_path, monkeypatch):
    drawn = _drawn_strings(defender_off, tmp_path, monkeypatch)
    assert "Antigravity" in drawn
    assert "Cyber Health Action Plan" in drawn
    versions = next(s for s in drawn if s.startswith("Engine "))
    assert versions.endswith(defender_off["scan"]["os_caption"])
