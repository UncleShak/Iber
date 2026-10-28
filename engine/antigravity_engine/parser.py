"""Load and validate scan.json into a ScanModel (s2.3 row 1, s2.4).

Validation order:
  1. file exists and is <= 2 MB
  2. strip one leading UTF-8 BOM (CLM fallback, s3.6), then parse as JSON
  3. schema_version major == "1"
  4. JSON Schema validation against scan.schema.json
Any failure raises ContractError.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from pydantic import ValidationError

from antigravity_engine.contract import ScanModel
from antigravity_engine.paths import schema_path

MAX_BYTES = 2 * 1024 * 1024
SUPPORTED_MAJOR = "1"
_BOM = b"\xef\xbb\xbf"
_MAX_MESSAGE = 200


class ContractError(Exception):
    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message if path is None else f"{path}: {message}")
        self.message = message
        self.path = path


def _reject_constant(name: str) -> None:
    raise ValueError(f"{name} is not valid JSON")


def load_json(path: str | Path) -> Any:
    """Steps 1-2: size check, BOM strip, strict JSON parse."""
    p = Path(path)
    if not p.is_file():
        raise ContractError(f"input missing or too large: {p} not found")
    size = p.stat().st_size
    if size > MAX_BYTES:
        raise ContractError(f"input missing or too large: {size} bytes exceeds {MAX_BYTES}")
    raw = p.read_bytes()
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    try:
        return json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    except UnicodeDecodeError as e:
        raise ContractError(f"not valid JSON: not UTF-8 ({e.reason} at byte {e.start})") from e
    except json.JSONDecodeError as e:
        raise ContractError(f"not valid JSON: {e.msg} at line {e.lineno} column {e.colno}") from e
    except ValueError as e:
        raise ContractError(f"not valid JSON: {e}") from e


@lru_cache(maxsize=None)
def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads(schema_path(schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_schema(data: Any, schema_name: str) -> None:
    """Step 4: raise ContractError for the most relevant schema error."""
    error = best_match(_validator(schema_name).iter_errors(data))
    if error is None:
        return
    message = error.message
    if len(message) > _MAX_MESSAGE:
        message = message[: _MAX_MESSAGE - 3] + "..."
    raise ContractError(message, path=error.json_path)


def check_major(data: Any) -> None:
    """Step 3. A missing or non-string version is left for the schema to report."""
    if not isinstance(data, dict):
        return
    version = data.get("schema_version")
    if isinstance(version, str) and version.split(".")[0] != SUPPORTED_MAJOR:
        raise ContractError(
            f"unsupported schema version {version!r}; engine supports {SUPPORTED_MAJOR}.x.x",
            path="$.schema_version",
        )


def parse_dict(d: Any) -> ScanModel:
    check_major(d)
    validate_schema(d, "scan.schema.json")
    try:
        return ScanModel.model_validate(d)
    except ValidationError as e:
        first = e.errors()[0]
        loc = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in first["loc"])
        raise ContractError(first["msg"], path="$" + loc) from e


def parse_path(path: str | Path) -> ScanModel:
    return parse_dict(load_json(path))
