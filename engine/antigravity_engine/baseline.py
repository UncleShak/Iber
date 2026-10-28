"""Load and validate software-baseline.json into a Baseline (s2.3 row 3, s2.8).

Load order:
  1. file exists, strip one leading UTF-8 BOM, parse as JSON
  2. JSON Schema validation against software-baseline.schema.json
  3. unique entry ids, regexes compile (re.IGNORECASE)
Any failure raises BaselineError.

Version helpers (s2.5.3): packaging.version.Version first, then a dotted-integer
tuple; None means "version not readable".
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from packaging.version import InvalidVersion, Version

from antigravity_engine.paths import baseline_schema_path

_BOM = b"\xef\xbb\xbf"
_DOTTED = re.compile(r"\d+(?:\.\d+)*")


class BaselineError(Exception):
    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message if path is None else f"{path}: {message}")
        self.message = message
        self.path = path


@dataclass(frozen=True)
class BaselineEntry:
    id: str
    display_name: str
    name_re: re.Pattern
    publisher_re: re.Pattern | None
    min_safe_version: str
    severity: str
    eol: bool
    eol_note: str | None
    update_hint: str
    source_url: str

    def matches(self, name: str, publisher: str | None = None) -> bool:
        if not self.name_re.match(name):
            return False
        if self.publisher_re is None:
            return True
        return bool(publisher) and bool(self.publisher_re.match(publisher))


@dataclass(frozen=True)
class Baseline:
    baseline_version: str
    checked_on: str
    win11_min_build: str
    win10_eos_date: str
    asr_recommended: frozenset[str]
    asr_names: dict[str, str]
    entries: tuple[BaselineEntry, ...]

    def match(self, name: str, publisher: str | None = None) -> BaselineEntry | None:
        """First entry whose regexes match, or None (app is not assessed)."""
        for entry in self.entries:
            if entry.matches(name, publisher):
                return entry
        return None


@lru_cache(maxsize=None)
def _validator() -> Draft202012Validator:
    schema = json.loads(baseline_schema_path().read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _compile(pattern: str, path: str) -> re.Pattern:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise BaselineError(f"invalid regex: {e}", path=path) from e


def _entry(d: dict[str, Any], i: int) -> BaselineEntry:
    match = d["match"]
    publisher = match.get("publisher_regex")
    return BaselineEntry(
        id=d["id"],
        display_name=d["display_name"],
        name_re=_compile(match["name_regex"], f"$.entries[{i}].match.name_regex"),
        publisher_re=None if publisher is None
        else _compile(publisher, f"$.entries[{i}].match.publisher_regex"),
        min_safe_version=d["min_safe_version"],
        severity=d["severity"],
        eol=d["eol"],
        eol_note=d.get("eol_note"),
        update_hint=d["update_hint"],
        source_url=d["source_url"],
    )


def baseline_from_dict(d: Any) -> Baseline:
    error = best_match(_validator().iter_errors(d))
    if error is not None:
        raise BaselineError(error.message, path=error.json_path)

    seen: set[str] = set()
    for i, e in enumerate(d["entries"]):
        if e["id"] in seen:
            raise BaselineError(f"duplicate entry id {e['id']!r}", path=f"$.entries[{i}].id")
        seen.add(e["id"])

    rules = d["asr"]["recommended"]
    return Baseline(
        baseline_version=d["baseline_version"],
        checked_on=d["checked_on"],
        win11_min_build=d["os"]["min_supported_build"]["win11"],
        win10_eos_date=d["os"]["win10_eos_date"],
        asr_recommended=frozenset(r["id"].lower() for r in rules),
        asr_names={r["id"].lower(): r["name"] for r in rules},
        entries=tuple(_entry(e, i) for i, e in enumerate(d["entries"])),
    )


def load_baseline(path: str | Path) -> Baseline:
    p = Path(path)
    if not p.is_file():
        raise BaselineError(f"baseline not found: {p}")
    raw = p.read_bytes()
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise BaselineError(f"baseline is not valid JSON: {e}") from e
    return baseline_from_dict(data)


def _dotted(s: str) -> tuple[int, ...] | None:
    """Leading dotted integers, e.g. "24.4.20220 build 7" -> (24, 4, 20220)."""
    m = _DOTTED.match(s.strip())
    if m is None:
        return None
    return tuple(int(part) for part in m.group(0).split("."))


def compare_versions(a: str, b: str) -> int | None:
    """-1 / 0 / 1 like a <=> b, or None if either side is not readable."""
    try:
        va, vb = Version(a), Version(b)
        return (va > vb) - (va < vb)
    except InvalidVersion:
        pass
    ta, tb = _dotted(a), _dotted(b)
    if ta is None or tb is None:
        return None
    width = max(len(ta), len(tb))
    ta += (0,) * (width - len(ta))
    tb += (0,) * (width - len(tb))
    return (ta > tb) - (ta < tb)


def is_below(installed: str, minimum: str) -> bool | None:
    """True if installed < minimum; None if the installed version is not readable."""
    c = compare_versions(installed, minimum)
    return None if c is None else c < 0
