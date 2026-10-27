# Installer Stubs
These stubs are used for Brick D isolation testing (`AG_STUB=1`).
- `collector-stub.ps1`: Simulates collection phases and copies `scan.stub.json`.
- `engine-stub.ps1`: Simulates engine processing and generates `report.json`, `evidence.json`, `report.html`, and `action-plan.pdf`.
- `*.stub.json`: Valid fixture data matching the shared contract.
