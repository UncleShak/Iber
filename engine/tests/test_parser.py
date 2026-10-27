import pytest

from antigravity_engine.contract import ScanModel, Status
from antigravity_engine.parser import MAX_BYTES, ContractError, parse_dict, parse_path
from conftest import FIXTURES

SCAN_FIXTURES = sorted(FIXTURES.glob("scan.*.json"))


def test_fixture_set_present():
    names = {p.name for p in SCAN_FIXTURES}
    assert {"scan.healthy.json", "scan.no-bitlocker.json", "scan.home-edition.json",
            "scan.defender-off.json", "scan.xss.json"} <= names


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_fixtures_parse(path):
    scan = parse_path(path)
    assert isinstance(scan, ScanModel)
    assert scan.schema_version.startswith("1.")
    assert len(scan.run_id) == 25


def test_healthy_typed_values():
    scan = parse_path(FIXTURES / "scan.healthy.json")
    assert scan.backup.status is Status.OK
    assert scan.protection.bitlocker.os_volume_protection == "on"
    assert scan.patch.hotfixes[0].kb == "KB5044285"
    assert scan.software.installed[1].name == "Adobe Acrobat Reader"


def test_unavailable_section_and_nulls():
    scan = parse_path(FIXTURES / "scan.defender-off.json")
    assert scan.protection.bitlocker.status is Status.UNAVAILABLE
    assert scan.protection.bitlocker.error == "Requires administrator rights"
    assert scan.backup.shadow_copy_count is None
    assert scan.recovery.winre_enabled is None


def test_xss_name_kept_verbatim():
    scan = parse_path(FIXTURES / "scan.xss.json")
    assert scan.software.installed[0].name == "<script>alert(1)</script><img src=x onerror=alert(2)>"


def test_unknown_keys_ignored(make_raw):
    raw = make_raw({"future_field": 1, "backup": {"new_probe": True}})
    scan = parse_dict(raw)
    assert not hasattr(scan, "future_field")
    assert not hasattr(scan.backup, "new_probe")


def test_optional_keys_may_be_absent(make_raw):
    raw = make_raw()
    del raw["protection"]["bitlocker"]["encryption_method"]
    del raw["protection"]["defender"]["third_party_av"]
    scan = parse_dict(raw)
    assert scan.protection.bitlocker.encryption_method is None
    assert scan.protection.defender.third_party_av is None


# --- step 1: existence and size ---------------------------------------------


def test_missing_file(tmp_path):
    with pytest.raises(ContractError, match="input missing or too large") as exc:
        parse_path(tmp_path / "nope.json")
    assert "nope.json" in exc.value.message
    assert exc.value.path is None


def test_directory_is_not_a_file(tmp_path):
    with pytest.raises(ContractError, match="input missing or too large"):
        parse_path(tmp_path)


def test_too_large(write_json):
    p = write_json(b" " * (MAX_BYTES + 1))
    with pytest.raises(ContractError, match=f"{MAX_BYTES + 1} bytes exceeds {MAX_BYTES}"):
        parse_path(p)


# --- step 2: BOM and JSON ----------------------------------------------------


def test_bom_prefixed_healthy_parses(write_json):
    p = write_json(b"\xef\xbb\xbf" + (FIXTURES / "scan.healthy.json").read_bytes())
    assert parse_path(p).run_id == "2026-11-14T16-42-07Z_0001"


def test_only_one_bom_is_stripped(write_json):
    p = write_json(b"\xef\xbb\xbf\xef\xbb\xbf" + (FIXTURES / "scan.healthy.json").read_bytes())
    with pytest.raises(ContractError, match="not valid JSON"):
        parse_path(p)


def test_bad_json_reports_position(write_json):
    p = write_json(b'{"schema_version": "1.0.0",\n  "run_id": }')
    with pytest.raises(ContractError, match=r"not valid JSON: Expecting value at line 2 column 13"):
        parse_path(p)


def test_empty_file(write_json):
    with pytest.raises(ContractError, match="not valid JSON"):
        parse_path(write_json(b""))


def test_nan_rejected(write_json):
    with pytest.raises(ContractError, match="NaN is not valid JSON"):
        parse_path(write_json(b'{"duration_ms": NaN}'))


def test_non_utf8_rejected(write_json):
    with pytest.raises(ContractError, match="not valid JSON: not UTF-8"):
        parse_path(write_json(b'{"a": "\xff"}'))


# --- step 3: major version ---------------------------------------------------


@pytest.mark.parametrize("version", ["2.0.0", "0.9.0", "10.0.0"])
def test_wrong_major_version(make_raw, version):
    with pytest.raises(ContractError, match="unsupported schema version") as exc:
        parse_dict(make_raw({"schema_version": version}))
    assert version in exc.value.message
    assert exc.value.path == "$.schema_version"


def test_newer_minor_accepted(make_raw):
    assert parse_dict(make_raw({"schema_version": "1.4.2"})).schema_version == "1.4.2"


def test_missing_version_reported_by_schema(make_raw):
    raw = make_raw()
    del raw["schema_version"]
    with pytest.raises(ContractError, match="'schema_version' is a required property") as exc:
        parse_dict(raw)
    assert exc.value.path == "$"


# --- step 4: JSON Schema -----------------------------------------------------


def test_wrong_type_reports_json_path(make_raw):
    with pytest.raises(ContractError, match="is not of type 'array'") as exc:
        parse_dict(make_raw({"patch": {"hotfixes": {}}}))
    assert exc.value.path == "$.patch.hotfixes"
    assert str(exc.value).startswith("$.patch.hotfixes: ")


def test_wrong_type_bool_as_string(make_raw):
    with pytest.raises(ContractError, match="'true' is not of type 'boolean'") as exc:
        parse_dict(make_raw({"host": {"is_admin": "true"}}))
    assert exc.value.path == "$.host.is_admin"


def test_nested_array_item_path(make_raw):
    raw = make_raw()
    raw["patch"]["hotfixes"][1]["kb"] = "5043080"
    with pytest.raises(ContractError, match="does not match") as exc:
        parse_dict(raw)
    assert exc.value.path == "$.patch.hotfixes[1].kb"


def test_missing_required_nullable_key(make_raw):
    raw = make_raw()
    del raw["backup"]["shadow_copy_count"]
    with pytest.raises(ContractError, match="'shadow_copy_count' is a required property") as exc:
        parse_dict(raw)
    assert exc.value.path == "$.backup"


def test_bad_status_enum(make_raw):
    with pytest.raises(ContractError) as exc:
        parse_dict(make_raw({"recovery": {"status": "broken"}}))
    assert exc.value.path == "$.recovery.status"


def test_bad_run_id(make_raw):
    with pytest.raises(ContractError) as exc:
        parse_dict(make_raw({"run_id": "today"}))
    assert exc.value.path == "$.run_id"


def test_top_level_not_object(write_json):
    with pytest.raises(ContractError, match="is not of type 'object'") as exc:
        parse_path(write_json(b"[1, 2]"))
    assert exc.value.path == "$"


def test_long_message_truncated(make_raw):
    with pytest.raises(ContractError) as exc:
        parse_dict(make_raw({"software": {"installed": "x" * 5000}}))
    assert len(exc.value.message) <= 200
    assert exc.value.message.endswith("...")
