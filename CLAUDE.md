# Antigravity - rules for Claude

Owner of this session's work: Brick A (Python assessment engine, `engine/`, `baseline/`).
Reference: docs/antigravity_manual_v1.1.md.

- Python only via `engine/.venv/Scripts/python.exe` (macOS dev machine: `engine/.venv/bin/python`); never bare `python`.
- No new dependencies beyond `engine/requirements.txt` / `engine/requirements-dev.txt`.
- No network code or network imports anywhere in `engine/` (no socket, http, urllib, requests, etc.).
- ASCII only in all files.
- Every scoring rule gets a test. No `assert True`.
- Do not edit `shared/contract/` or `shared/fixtures/` unless the user explicitly asks.
- Run the test suite and show the output before saying anything is done.
