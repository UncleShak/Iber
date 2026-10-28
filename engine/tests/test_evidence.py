"""Evidence bundle and --verify (s2.14). s2.14.4 table first, then edge cases."""

import copy
import hashlib
import json

import pytest

from antigravity_engine import __main__ as cli
from antigravity_engine import evidence
from antigravity_engine.parser import validate_schema
from conftest import FIXTURES, ROOT

SCANS = sorted(FIXTURES.glob("scan.*.json"))
BASELINE = ROOT / "baseline" / "software-baseline.json"


def _produce(scan_path, out_dir) -> dict:
    assert cli.main(["--in", str(scan_path), "--out", str(out_dir), "--json-only"]) == 0
    return json.loads((out_dir / "evidence.json").read_text(encoding="utf-8"))


def _rehash(bundle: dict) -> dict:
    """What a careful forger does after editing: recompute every hash and the ID."""
    bundle["scan_sha256"] = evidence.canonical_hash(bundle["scan"])
    bundle["report_sha256"] = evidence.canonical_hash(bundle["report"])
    bundle["evidence_id"] = evidence.evidence_id(bundle["report_sha256"])
    return bundle


def _verify(bundle, tmp_path, capsys, *extra) -> tuple[int, str]:
    path = tmp_path / "check.json"
    if isinstance(bundle, bytes):
        path.write_bytes(bundle)
    else:
        path.write_text(json.dumps(bundle), encoding="utf-8")
    capsys.readouterr()
    code = cli.main(["--verify", str(path), "--baseline", str(BASELINE), *extra])
    return code, capsys.readouterr().out.strip()


@pytest.fixture
def healthy(tmp_path) -> dict:
    return _produce(FIXTURES / "scan.healthy.json", tmp_path / "produced")


@pytest.fixture
def defender_off(tmp_path) -> dict:
    return _produce(FIXTURES / "scan.defender-off.json", tmp_path / "produced")


# --- s2.14.4 ---


@pytest.mark.parametrize("scan_path", SCANS, ids=lambda p: p.name)
def test_unchanged_bundle_verifies(scan_path, tmp_path, capsys):
    bundle = _produce(scan_path, tmp_path / "produced")
    code, out = _verify(bundle, tmp_path, capsys)
    assert code == evidence.VERIFIED == 0
    assert out.startswith("VERIFIED - report matches the measured scan.")
    assert f"Evidence ID {bundle['evidence_id']}" in out


def test_status_edit_without_rehash_is_report_edited(defender_off, tmp_path, capsys):
    cat = next(c for c in defender_off["report"]["categories"] if c["status"] == "red")
    cat["status"] = "green"
    code, out = _verify(defender_off, tmp_path, capsys)
    assert code == evidence.TAMPERED == 5
    assert out == "TAMPERED: report edited"


def test_status_edit_with_rehash_does_not_match_scan(defender_off, tmp_path, capsys):
    idx, cat = next(
        (i, c) for i, c in enumerate(defender_off["report"]["categories"]) if c["status"] == "red"
    )
    cat["status"] = "green"
    code, out = _verify(_rehash(defender_off), tmp_path, capsys)
    assert code == 5
    assert out == (
        "TAMPERED: report does not match the scan "
        f"(first difference: $.categories[{idx}].status)"
    )


def test_scan_edit_with_rehash_does_not_match_report(healthy, tmp_path, capsys):
    defender = healthy["scan"]["protection"]["defender"]
    assert defender["realtime_enabled"] is True
    defender["realtime_enabled"] = False
    code, out = _verify(_rehash(healthy), tmp_path, capsys)
    assert code == 5
    assert out.startswith("TAMPERED: report does not match the scan (first difference: $.")


def test_scan_edit_that_cannot_change_the_report_still_verifies(defender_off, tmp_path, capsys):
    # s2.14 honest scope: the verifier proves report == rules(scan), not that the
    # scan is genuine. Antivirus is already off, so real-time on/off rates the same.
    defender = defender_off["scan"]["protection"]["defender"]
    assert defender["antivirus_enabled"] is False
    defender["realtime_enabled"] = True
    code, out = _verify(_rehash(defender_off), tmp_path, capsys)
    assert code == 0, out


def test_scan_edit_without_rehash_is_scan_edited(defender_off, tmp_path, capsys):
    defender_off["scan"]["protection"]["defender"]["realtime_enabled"] = True
    code, out = _verify(defender_off, tmp_path, capsys)
    assert (code, out) == (5, "TAMPERED: scan edited")


def test_deleted_top_fix_with_rehash_is_tampered(defender_off, tmp_path, capsys):
    assert defender_off["report"]["top_fixes"]
    del defender_off["report"]["top_fixes"][0]
    code, out = _verify(_rehash(defender_off), tmp_path, capsys)
    assert code == 5
    assert out.startswith("TAMPERED: report does not match the scan (first difference: $.top_fixes")


def test_other_engine_version_cannot_verify(healthy, tmp_path, capsys):
    healthy["engine_version"] = "9.9.0"
    code, out = _verify(healthy, tmp_path, capsys)
    assert code == evidence.CANNOT_VERIFY == 6
    assert out == "CANNOT_VERIFY: different engine/baseline - use verifier v9.9"


@pytest.mark.parametrize("scan_path", SCANS, ids=lambda p: p.name)
def test_same_scan_twice_gives_same_report_hash(scan_path, tmp_path):
    a = _produce(scan_path, tmp_path / "a")
    b = _produce(scan_path, tmp_path / "b")
    assert a["report"]["generated_at"] and b["report"]["generated_at"]
    for bundle in (a, b):
        bundle["report"].pop("generated_at")
    assert evidence.canonical_hash(a["report"]) == evidence.canonical_hash(b["report"])
    assert a["scan_sha256"] == b["scan_sha256"]
    assert a["baseline_sha256"] == b["baseline_sha256"]


# --- the bundle ---


def test_bundle_fields_and_hashes(healthy):
    scan = json.loads((FIXTURES / "scan.healthy.json").read_text(encoding="utf-8"))
    validate_schema(healthy, "evidence.schema.json")
    assert healthy["evidence_version"] == "1.0.0"
    assert healthy["scan"] == scan
    assert healthy["run_id"] == scan["run_id"] == healthy["report"]["run_id"]
    assert healthy["engine_version"] == healthy["report"]["engine_version"]
    assert healthy["baseline_version"] == healthy["report"]["baseline_version"]
    assert healthy["scan_sha256"] == evidence.canonical_hash(scan)
    assert healthy["report_sha256"] == evidence.canonical_hash(healthy["report"])
    assert healthy["evidence_id"] == "AG-" + healthy["report_sha256"][7:19]
    assert healthy["baseline_sha256"] == evidence.baseline_hash(BASELINE)


def test_embedded_report_equals_report_json(tmp_path):
    out = tmp_path / "out"
    bundle = _produce(FIXTURES / "scan.healthy.json", out)
    assert bundle["report"] == json.loads((out / "report.json").read_text(encoding="utf-8"))


def test_evidence_json_is_ascii_on_disk(tmp_path):
    out = tmp_path / "out"
    _produce(FIXTURES / "scan.xss.json", out)
    (out / "evidence.json").read_bytes().decode("ascii")


def test_canonical_hash_rule():
    obj = {"b": [1, "\u00e9"], "a": None}
    text = '{"a":null,"b":[1,"\u00e9"]}'
    assert evidence.canonical_hash(obj) == (
        "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    )
    assert evidence.canonical_hash({"a": None, "b": [1, "\u00e9"]}) == evidence.canonical_hash(obj)


def test_baseline_hash_ignores_line_endings(tmp_path):
    crlf = tmp_path / "crlf.json"
    crlf.write_bytes(BASELINE.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert evidence.baseline_hash(crlf) == evidence.baseline_hash(BASELINE)


def test_bad_input_writes_no_evidence(tmp_path, write_json):
    out = tmp_path / "out"
    assert cli.main(["--in", str(write_json(b"{bad")), "--out", str(out)]) == 2
    assert not (out / "evidence.json").exists()


def test_evidence_id_in_html_footer(tmp_path):
    out = tmp_path / "out"
    assert cli.main(["--in", str(FIXTURES / "scan.healthy.json"), "--out", str(out)]) == 0
    bundle = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
    assert f"Evidence ID {bundle['evidence_id']}" in (out / "report.html").read_text("utf-8")


def test_evidence_id_in_pdf_footer(tmp_path, monkeypatch):
    from antigravity_engine.render import pdf

    drawn = []
    real = pdf._text
    monkeypatch.setattr(pdf, "_text", lambda c, x, y, text, *a, **k: (
        drawn.append(text), real(c, x, y, text, *a, **k)))
    report = json.loads((FIXTURES / "report.healthy.json").read_text(encoding="utf-8"))
    assert pdf.render(report, tmp_path / "a.pdf", evidence_id="AG-0123456789ab") == 1
    assert any(t.endswith("Evidence ID AG-0123456789ab") for t in drawn)


def test_no_evidence_id_without_bundle():
    from antigravity_engine.render import html

    report = json.loads((FIXTURES / "report.healthy.json").read_text(encoding="utf-8"))
    assert "Evidence ID" not in html.render_string(report)


# --- verifier step 1: not an evidence file ---


@pytest.mark.parametrize("raw", [b"{bad", b"[]", b"\xff\xfe", b'"text"'])
def test_unreadable_file_cannot_verify(raw, tmp_path, capsys):
    assert _verify(raw, tmp_path, capsys) == (6, evidence.NOT_EVIDENCE)


def test_missing_file_cannot_verify(tmp_path, capsys):
    code = cli.main(["--verify", str(tmp_path / "nope.json"), "--baseline", str(BASELINE)])
    assert (code, capsys.readouterr().out.strip()) == (6, evidence.NOT_EVIDENCE)


def test_oversize_file_cannot_verify(healthy, tmp_path, capsys):
    healthy["padding"] = "x" * evidence.MAX_BYTES
    assert _verify(healthy, tmp_path, capsys) == (6, evidence.NOT_EVIDENCE)


@pytest.mark.parametrize("version", ["2.0.0", "0.9.0", 1])
def test_other_evidence_major_cannot_verify(version, healthy, tmp_path, capsys):
    healthy["evidence_version"] = version
    assert _verify(healthy, tmp_path, capsys) == (6, evidence.NOT_EVIDENCE)


@pytest.mark.parametrize("field", ["scan", "report", "report_sha256", "evidence_id"])
def test_missing_field_cannot_verify(field, healthy, tmp_path, capsys):
    del healthy[field]
    assert _verify(healthy, tmp_path, capsys) == (6, evidence.NOT_EVIDENCE)


def test_malformed_hash_cannot_verify(healthy, tmp_path, capsys):
    healthy["scan_sha256"] = "md5:abc"
    assert _verify(healthy, tmp_path, capsys) == (6, evidence.NOT_EVIDENCE)


# --- verifier steps 2-4: edge cases ---


def test_edited_evidence_id_is_tampered(healthy, tmp_path, capsys):
    healthy["evidence_id"] = "AG-000000000000"
    assert _verify(healthy, tmp_path, capsys) == (5, "TAMPERED: evidence ID edited")


def test_other_baseline_cannot_verify(healthy, tmp_path, capsys, write_json):
    other = json.loads(BASELINE.read_text(encoding="utf-8"))
    other["baseline_version"] = "2099-01-01"
    path = write_json(other, "other-baseline.json")
    code, out = _verify(healthy, tmp_path, capsys, "--baseline", str(path))
    assert code == 6
    assert out.startswith("CANNOT_VERIFY: different engine/baseline")


def test_missing_baseline_cannot_verify(healthy, tmp_path, capsys):
    code, out = _verify(healthy, tmp_path, capsys, "--baseline", str(tmp_path / "none.json"))
    assert code == 6
    assert out.startswith("CANNOT_VERIFY: different engine/baseline")


def test_patch_release_of_same_minor_still_verifies(healthy, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(evidence, "__version__", "0.1.9")
    code, out = _verify(healthy, tmp_path, capsys)
    assert code == 0, out


def test_other_minor_cannot_verify(healthy, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(evidence, "__version__", "0.2.0")
    assert _verify(healthy, tmp_path, capsys) == (
        6, "CANNOT_VERIFY: different engine/baseline - use verifier v0.1"
    )


def test_invalid_embedded_scan_with_rehash_is_tampered(healthy, tmp_path, capsys):
    healthy["scan"]["schema_version"] = "1"
    code, out = _verify(_rehash(healthy), tmp_path, capsys)
    assert code == 5
    assert out.startswith("TAMPERED: report does not match the scan (first difference: $.scan")


def test_generated_at_edit_with_rehash_still_verifies(healthy, tmp_path, capsys):
    healthy["report"]["generated_at"] = "2030-01-01T00:00:00Z"
    code, out = _verify(_rehash(healthy), tmp_path, capsys)
    assert code == 0, out


def test_added_report_key_with_rehash_is_tampered(healthy, tmp_path, capsys):
    healthy["report"]["note"] = "approved by insurer"
    code, out = _verify(_rehash(healthy), tmp_path, capsys)
    assert (code, out) == (
        5, "TAMPERED: report does not match the scan (first difference: $.note)"
    )


def test_verified_message_counts_not_checked_rows(tmp_path, capsys):
    bundle = _produce(FIXTURES / "scan.home-edition.json", tmp_path / "produced")
    rows = [r for c in bundle["report"]["categories"] for r in c["evidence"]]
    n = sum(r.get("status") in ("unavailable", "failed") for r in rows)
    code, out = _verify(bundle, tmp_path, capsys)
    assert code == 0
    assert out.endswith(f"Collected 14 Nov 2026. Not checked: {n} items")


def test_verify_ignores_in_and_out(healthy, tmp_path, capsys):
    path = tmp_path / "e.json"
    path.write_text(json.dumps(healthy), encoding="utf-8")
    code = cli.main(["--verify", str(path), "--baseline", str(BASELINE),
                     "--in", str(tmp_path / "nope.json"), "--out", str(tmp_path / "never")])
    assert code == 0
    assert not (tmp_path / "never").exists()


# --- first_difference ---


@pytest.mark.parametrize(
    ("a", "b", "path"),
    [
        ({"x": 1}, {"x": 1}, None),
        ({"x": 1}, {"x": 2}, "$.x"),
        ({"x": 1}, {"y": 1}, "$.x"),
        ({"x": [1, 2]}, {"x": [1]}, "$.x[1]"),
        ({"x": [{"s": "red"}]}, {"x": [{"s": "green"}]}, "$.x[0].s"),
        ({"x": 1}, {"x": True}, "$.x"),
        ({"x": 1}, {"x": 1.0}, "$.x"),
    ],
)
def test_first_difference(a, b, path):
    assert evidence.first_difference(copy.deepcopy(a), b) == path
