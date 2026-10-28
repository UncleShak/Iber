"""Contract tests for shared/contract (manual §0.5–§0.7, Appendix A.1, A.3).

Run (cwd: antigravity):
    engine\\.venv\\Scripts\\python -B -m pytest -q -p no:cacheprovider shared\\contract\\tests
"""

import copy
import json
import re
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

CONTRACT = Path(__file__).resolve().parents[1]
FIXTURES = CONTRACT.parent / "fixtures"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

FIXTURE_NAMES = ["healthy", "no-bitlocker", "home-edition", "defender-off", "xss"]

# RPT-07 (§7.6): exact attack string the HTML report and UI must show literally.
RPT07_PAYLOAD = "<script>alert(1)</script><img src=x onerror=alert(2)>"

# Field sets from the §0.6 table. Every fixture key and schema property must be in here.
SECTION = {"status", "error"}
MANUAL_KEYS = {
    "": {"schema_version", "run_id", "collected_at", "collector_version", "duration_ms",
         "host", "backup", "patch", "software", "protection", "recovery"},
    "host": {"hostname_hash", "os_caption", "os_build", "os_edition", "is_admin", "ps_version"},
    "backup": SECTION | {"file_history_enabled", "file_history_last_backup",
                         "windows_backup_last_success", "onedrive_kfm_folders",
                         "shadow_copy_count", "third_party_agents"},
    "patch": SECTION | {"hotfix_count", "latest_hotfix_installed_on", "days_since_latest_hotfix",
                        "hotfixes", "pending_reboot"},
    "patch.hotfixes[]": {"kb", "installed_on"},
    "software": SECTION | {"installed"},
    "software.installed[]": {"name", "version", "publisher"},
    "protection": {"bitlocker", "defender", "cfa", "asr"},
    "protection.bitlocker": SECTION | {"os_volume_protection", "os_volume_encryption_pct",
                                       "encryption_method"},
    "protection.defender": SECTION | {"antivirus_enabled", "realtime_enabled", "tamper_protected",
                                      "signature_age_days", "third_party_av"},
    "protection.cfa": SECTION | {"mode"},
    "protection.asr": SECTION | {"rules"},
    "protection.asr.rules[]": {"id", "action"},
    "recovery": SECTION | {"winre_enabled", "system_restore_enabled", "restore_point_count",
                           "latest_restore_point"},
}
# ⬜ (optional) rows in §0.6; every other key is required.
OPTIONAL_KEYS = {"protection.bitlocker": {"encryption_method"},
                 "protection.defender": {"third_party_av"}}

EVIDENCE_KEYS = {"evidence_version", "run_id", "created_at", "engine_version", "baseline_version",
                 "baseline_sha256", "scan", "report", "scan_sha256", "report_sha256", "evidence_id"}


def load_json(path: Path):
    assert path.exists(), f"{path.name} does not exist"
    assert path.stat().st_size > 0, f"{path.name} is empty (not written yet)"
    with path.open("rb") as f:
        raw = f.read()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path.name} has a UTF-8 BOM (§0.5: no BOM)"
    return json.loads(raw.decode("utf-8"))


def scan_schema():
    return load_json(CONTRACT / "scan.schema.json")


def evidence_schema():
    return load_json(CONTRACT / "evidence.schema.json")


def fixture(name):
    return load_json(FIXTURES / f"scan.{name}.json")


def errors(schema, instance):
    return list(Draft202012Validator(schema).iter_errors(instance))


def node_at(obj, path):
    """Walk a dotted path; a trailing [] means 'every item of this array'."""
    nodes = [obj]
    if not path:
        return nodes
    for part in path.split("."):
        many = part.endswith("[]")
        key = part[:-2] if many else part
        nodes = [n[key] for n in nodes]
        if many:
            nodes = [item for n in nodes for item in n]
    return nodes


def schema_node(schema, path):
    """Return (properties, required) of the schema object at a dotted path, merging $defs/section."""
    node = schema
    for part in path.split(".") if path else []:
        many = part.endswith("[]")
        node = node["properties"][part[:-2] if many else part]
        if many:
            node = node["items"]
    props = set(node.get("properties", {}))
    required = set(node.get("required", []))
    for sub in node.get("allOf", []):
        if sub.get("$ref") == "#/$defs/section":
            section = schema["$defs"]["section"]
            props |= set(section["properties"])
            required |= set(section["required"])
    return props, required


# ---------- 1. schemas are valid draft 2020-12 ----------

@pytest.mark.parametrize("loader", [scan_schema, evidence_schema], ids=["scan", "evidence"])
def test_schema_is_valid_draft_2020_12(loader):
    schema = loader()
    assert schema["$schema"] == DRAFT_2020_12
    Draft202012Validator.check_schema(schema)


# ---------- 2. every fixture validates ----------

@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_validates_against_scan_schema(name):
    errs = errors(scan_schema(), fixture(name))
    assert errs == [], [f"{list(e.absolute_path)}: {e.message}" for e in errs]


# ---------- 3. only §0.6 fields (automated PRV-05) ----------

@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_keys_match_manual_table(name):
    data = fixture(name)
    for path, expected in MANUAL_KEYS.items():
        for node in node_at(data, path):
            assert set(node) <= expected, f"{name} {path or '<root>'}: extra keys {set(node) - expected}"
            missing = expected - OPTIONAL_KEYS.get(path, set()) - set(node)
            assert not missing, f"{name} {path or '<root>'}: missing keys {missing}"


@pytest.mark.parametrize("path", list(MANUAL_KEYS))
def test_schema_properties_match_manual_table(path):
    props, required = schema_node(scan_schema(), path)
    assert props == MANUAL_KEYS[path], f"{path or '<root>'}: schema {props ^ MANUAL_KEYS[path]}"
    assert required == MANUAL_KEYS[path] - OPTIONAL_KEYS.get(path, set())


# ---------- 4. schema rejects bad input ----------

def _set(path, value):
    def mutate(d):
        *parents, last = path.split(".")
        for p in parents:
            d = d[p]
        d[last] = value
    return mutate


def _delete(path):
    def mutate(d):
        *parents, last = path.split(".")
        for p in parents:
            d = d[p]
        del d[last]
    return mutate


NEGATIVE_CASES = {
    "major-version-2": _set("schema_version", "2.0.0"),
    "raw-hostname": _set("host.hostname_hash", "DESKTOP-ABC123"),
    "bad-run-id": _set("run_id", "2026-11-14 16:42:07"),
    "status-error": _set("backup.status", "error"),
    "onedrive-downloads": _set("backup.onedrive_kfm_folders", ["Downloads"]),
    "eleven-hotfixes": _set("patch.hotfixes", [{"kb": f"KB50000{i:02d}", "installed_on": "2026-11-01"}
                                               for i in range(11)]),
    "missing-nullable-key": _delete("recovery.restore_point_count"),
    "asr-action-enabled": _set("protection.asr.rules", [{"id": "d4f940ab-401b-4efc-aadc-ad5f3c50688a",
                                                         "action": "enabled"}]),
    "encryption-101": _set("protection.bitlocker.os_volume_encryption_pct", 101),
    "error-too-long": _set("patch.error", "x" * 201),
    # PowerShell 5.1 failure modes (§3.8): local-offset dates, /Date()/ dates,
    # empty pipeline serialised as null, single item unwrapped from its array.
    "offset-timestamp": _set("collected_at", "2026-11-14T18:42:07+02:00"),
    "ms-json-date": _set("backup.file_history_last_backup", "/Date(1731600000000)/"),
    "null-kfm-folders": _set("backup.onedrive_kfm_folders", None),
    "null-backup-agents": _set("backup.third_party_agents", None),
    "null-hotfixes": _set("patch.hotfixes", None),
    "null-installed": _set("software.installed", None),
    "null-asr-rules": _set("protection.asr.rules", None),
    "unwrapped-hotfix": _set("patch.hotfixes", {"kb": "KB5044285", "installed_on": "2026-11-05"}),
    "unwrapped-app": _set("software.installed", {"name": "7-Zip", "version": "24.08", "publisher": "Igor Pavlov"}),
}


@pytest.mark.parametrize("case", list(NEGATIVE_CASES))
def test_schema_rejects_bad_input(case):
    data = copy.deepcopy(fixture("healthy"))
    NEGATIVE_CASES[case](data)
    assert errors(scan_schema(), data), f"schema accepted bad input: {case}"


# ---------- 5. each fixture holds what its name promises ----------

def test_healthy_fixture():
    d = fixture("healthy")
    assert d["host"]["is_admin"] is True
    statuses = [d[s]["status"] for s in ("backup", "patch", "software", "recovery")]
    statuses += [d["protection"][s]["status"] for s in ("bitlocker", "defender", "cfa", "asr")]
    assert set(statuses) == {"ok"}


def test_no_bitlocker_fixture():
    bl = fixture("no-bitlocker")["protection"]["bitlocker"]
    assert bl["status"] == "ok"
    assert bl["os_volume_protection"] == "off"


def test_home_edition_fixture():
    d = fixture("home-edition")
    assert d["host"]["os_edition"] == "Core"
    assert d["host"]["is_admin"] is True  # unavailable because of Home, not missing rights
    bl = d["protection"]["bitlocker"]
    assert bl["status"] == "unavailable"
    assert bl["error"] == "BitLocker management not available on Windows Home"
    assert bl["os_volume_protection"] is None


def test_defender_off_fixture():
    d = fixture("defender-off")
    assert d["host"]["is_admin"] is False
    dfn = d["protection"]["defender"]
    assert dfn["antivirus_enabled"] is False and dfn["realtime_enabled"] is False
    assert d["protection"]["bitlocker"]["status"] == "unavailable"
    assert d["protection"]["bitlocker"]["error"] == "Requires administrator rights"
    assert d["backup"]["shadow_copy_count"] is None
    assert d["recovery"]["winre_enabled"] is None
    assert d["recovery"]["restore_point_count"] is None


def test_xss_fixture_carries_rpt07_payload():
    d = fixture("xss")
    assert RPT07_PAYLOAD in [app["name"] for app in d["software"]["installed"]]
    # Unmatched apps are never rendered (§2.5.3), so also plant it where the report shows text.
    assert d["host"]["os_caption"] == RPT07_PAYLOAD
    assert RPT07_PAYLOAD in d["backup"]["third_party_agents"]
    # §2.5.4: AV off + third_party_av set renders "Protected by <third_party_av>".
    dfn = d["protection"]["defender"]
    assert dfn["third_party_av"] == RPT07_PAYLOAD
    assert dfn["antivirus_enabled"] is False


# ---------- 6. POPIA: no personal data in fixtures ----------

OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
POPIA_PATTERNS = {
    "ipv4": re.compile(rf"\b{OCTET}(?:\.{OCTET}){{3}}\b"),
    "mac": re.compile(r"\b[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}\b"),
    "windows-path": re.compile(r"[A-Za-z]:\\|\\\\"),
    "user-profile": re.compile(r"(?i)[\\/]users[\\/]"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "raw-hostname": re.compile(r"\b(?:DESKTOP|LAPTOP|WIN)-[A-Z0-9]{4,}\b"),
    "env-var": re.compile(r"%\w+%"),
}


def _strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)
    elif isinstance(obj, str):
        yield obj


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_has_no_personal_data(name):
    for text in _strings(fixture(name)):
        for kind, pattern in POPIA_PATTERNS.items():
            assert not pattern.search(text), f"{name}: looks like {kind}: {text!r}"


# ---------- 7. run ids ----------

def test_run_ids_unique_and_match_collected_at():
    run_ids = []
    for name in FIXTURE_NAMES:
        d = fixture(name)
        stamp = d["run_id"].split("_")[0]
        date, time = stamp.split("T")
        assert f"{date}T{time.replace('-', ':')}" == d["collected_at"], name
        run_ids.append(d["run_id"])
    assert len(set(run_ids)) == len(run_ids)


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_patch_fields_consistent(name):
    d = fixture(name)
    p = d["patch"]
    assert p["hotfix_count"] >= len(p["hotfixes"])
    assert p["latest_hotfix_installed_on"] == max(h["installed_on"] for h in p["hotfixes"])
    age = date.fromisoformat(d["collected_at"][:10]) - date.fromisoformat(p["latest_hotfix_installed_on"])
    assert p["days_since_latest_hotfix"] == age.days


# ---------- 8. evidence bundle schema ----------

def _bundle():
    report_hash = "sha256:" + "7f3a9c2e41b0" + "0" * 52
    return {
        "evidence_version": "1.0.0",
        "run_id": "2026-11-14T16-42-07Z_0001",
        "created_at": "2026-11-14T16:42:09Z",
        "engine_version": "0.1.0",
        "baseline_version": "2026-11-01",
        "baseline_sha256": "sha256:" + "a" * 64,
        "scan": fixture("healthy"),
        "report": {"schema_version": "1.0.0"},
        "scan_sha256": "sha256:" + "b" * 64,
        "report_sha256": report_hash,
        "evidence_id": "AG-7f3a9c2e41b0",
    }


def test_evidence_schema_required_keys_match_manual():
    assert set(evidence_schema()["required"]) == EVIDENCE_KEYS


def test_evidence_schema_accepts_valid_bundle():
    errs = errors(evidence_schema(), _bundle())
    assert errs == [], [e.message for e in errs]


EVIDENCE_NEGATIVE = {
    "bad-evidence-id": _set("evidence_id", "AG-XYZ"),
    "evidence-version-2": _set("evidence_version", "2.0.0"),
    "hash-without-prefix": _set("scan_sha256", "b" * 64),
    "missing-evidence-id": _delete("evidence_id"),
}


@pytest.mark.parametrize("case", list(EVIDENCE_NEGATIVE))
def test_evidence_schema_rejects_bad_bundle(case):
    bundle = _bundle()
    EVIDENCE_NEGATIVE[case](bundle)
    assert errors(evidence_schema(), bundle), f"evidence schema accepted: {case}"


# ---------- 9. types.ts stays in step with the schema ----------

TS_INTERFACES = {
    "ScanJson": "",
    "ScanHost": "host",
    "BackupSection": "backup",
    "PatchSection": "patch",
    "Hotfix": "patch.hotfixes[]",
    "SoftwareSection": "software",
    "InstalledApp": "software.installed[]",
    "ProtectionBlock": "protection",
    "BitLockerSection": "protection.bitlocker",
    "DefenderSection": "protection.defender",
    "CfaSection": "protection.cfa",
    "AsrSection": "protection.asr",
    "AsrRule": "protection.asr.rules[]",
    "RecoverySection": "recovery",
}


def parse_ts_interfaces():
    path = CONTRACT / "types.ts"
    assert path.stat().st_size > 0, "types.ts is empty (not written yet)"
    text = path.read_text(encoding="utf-8")
    found = {}
    for m in re.finditer(r"export interface (\w+)(?: extends (\w+))? \{(.*?)\n\}", text, re.S):
        name, base, body = m.groups()
        fields = dict(re.findall(r"^\s*(\w+)(\??):", body, re.M))
        found[name] = (base, fields)
    # Flatten `extends` (one level is all we use).
    flat = {}
    for name, (base, fields) in found.items():
        merged = dict(found[base][1]) if base else {}
        merged.update(fields)
        flat[name] = merged
    return flat


@pytest.mark.parametrize("iface", list(TS_INTERFACES))
def test_types_ts_matches_schema(iface):
    ts = parse_ts_interfaces()
    assert iface in ts, f"types.ts has no interface {iface}"
    props, required = schema_node(scan_schema(), TS_INTERFACES[iface])
    assert set(ts[iface]) == props, f"{iface}: differs on {set(ts[iface]) ^ props}"
    optional_in_ts = {k for k, q in ts[iface].items() if q == "?"}
    assert optional_in_ts == props - required, f"{iface}: optional mismatch"


def parse_ts_types():
    """({interface: {field: type text}}, {alias: set of string literals}), `extends` flattened."""
    text = (CONTRACT / "types.ts").read_text(encoding="utf-8")
    aliases = {}
    for name, rhs in re.findall(r"^export type (\w+) = (.+?);", text, re.M):
        parts = [x.strip() for x in rhs.split("|")]
        if all(re.fullmatch(r"'[^']*'", x) for x in parts):
            aliases[name] = {x.strip("'") for x in parts}
    blocks = {}
    for m in re.finditer(r"export interface (\w+)(?: extends (\w+))? \{(.*?)\n\}", text, re.S):
        name, base, body = m.groups()
        blocks[name] = (base, dict(re.findall(r"^\s*(\w+)\??:\s*(.+?);", body, re.M)))
    flat = {n: {**(blocks[b][1] if b else {}), **f} for n, (b, f) in blocks.items()}
    return flat, aliases


def ts_shape(type_text, aliases):
    """(accepts null?, set of allowed string literals or None)."""
    parts = [x.strip() for x in type_text.split("|")]
    literals = set()
    for part in parts:
        part = part.removesuffix("[]")
        if part in aliases:
            literals |= aliases[part]
        elif re.fullmatch(r"'[^']*'", part):
            literals.add(part.strip("'"))
    return "null" in parts, literals or None


def schema_shape(schema, prop):
    """(accepts null?, set of allowed string literals or None); looks inside arrays and $defs refs."""
    def resolve(node):
        ref = node.get("$ref", "")
        return schema["$defs"][ref.split("/")[-1]] if ref.startswith("#/$defs/") else node
    node = resolve(prop)
    if node.get("type") == "array":
        node = resolve(node["items"])
    branches = [resolve(b) for b in node.get("anyOf", [node])]
    nullable = any(b.get("type") == "null" or "null" in (b.get("type") or []) or None in b.get("enum", [])
                   for b in branches)
    literals = {v for b in branches for v in b.get("enum", []) if v is not None}
    return nullable, literals or None


@pytest.mark.parametrize("iface", list(TS_INTERFACES))
def test_types_ts_nullability_and_enums_match_schema(iface):
    schema = scan_schema()
    ts_fields, aliases = parse_ts_types()
    node = schema
    for part in TS_INTERFACES[iface].split(".") if TS_INTERFACES[iface] else []:
        many = part.endswith("[]")
        node = node["properties"][part[:-2] if many else part]
        if many:
            node = node["items"]
    props = dict(node.get("properties", {}))
    if any(sub.get("$ref") == "#/$defs/section" for sub in node.get("allOf", [])):
        props.update(schema["$defs"]["section"]["properties"])
    for key, prop in props.items():
        if "properties" in prop or "allOf" in prop:
            continue  # nested object: checked through its own interface
        assert ts_shape(ts_fields[iface][key], aliases) == schema_shape(schema, prop), \
            f"{iface}.{key}: TS {ts_fields[iface][key]!r} vs schema {prop}"


def test_types_ts_evidence_bundle_matches_schema():
    ts = parse_ts_interfaces()
    assert "EvidenceBundle" in ts, "types.ts has no interface EvidenceBundle"
    assert set(ts["EvidenceBundle"]) == set(evidence_schema()["properties"])
    assert not any(q == "?" for q in ts["EvidenceBundle"].values())
