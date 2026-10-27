"""Schema gate (s6.3): validate.py scan|report <file>

Prints "VALID <kind> <version>" and exits 0, or
"INVALID <json-path>: <message>" and exits 1.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from antigravity_engine.parser import (  # noqa: E402
    ContractError,
    check_major,
    load_json,
    parse_dict,
    validate_schema,
)


def validate(kind: str, path: str) -> str:
    """Return the schema_version of a valid file; raise ContractError otherwise."""
    data = load_json(path)
    if kind == "scan":
        return parse_dict(data).schema_version
    check_major(data)
    validate_schema(data, "report.schema.json")
    return data["schema_version"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="validate.py", description=__doc__.splitlines()[0])
    ap.add_argument("kind", choices=["scan", "report"])
    ap.add_argument("file")
    args = ap.parse_args(argv)
    try:
        version = validate(args.kind, args.file)
    except ContractError as e:
        print(f"INVALID {e.path or '$'}: {e.message}")
        return 1
    print(f"VALID {args.kind} {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
