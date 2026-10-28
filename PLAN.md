# Brick A (engine) build plan

Each phase is done only when its gate passes and the test output has been shown.

- [x] 1. Contract + parser - gate: all shared/fixtures/scan.*.json load into ScanModel; malformed or wrong-major input raises a clear error (tests).
- [x] 2. Baseline - gate: baseline/software-baseline.json validates against its schema, has >= 10 SMME apps, and loads via baseline.py (tests).
- [x] 3. Scoring infra - gate: CategoryResult/EvidenceRow, clock ("now" = collected_at), aggregator overall RAG and top-3 ranking pass test_ranking.py.
- [x] 4. Backup + patch scoring - gate: test_backup.py and test_patch.py cover every rule in s2.5.1 and s2.5.2, incl. unavailable/failed.
- [x] 5. Software + recovery scoring - gate: test_software.py and test_recovery.py cover every rule in s2.5.3 and s2.5.5.
- [x] 6. Protection scoring - gate: test_protection.py covers s2.5.4; home-edition fixture is amber, no-bitlocker and defender-off are red.
- [x] 7. CLI - gate: test_cli.py: --in/--out/--baseline/--json-only/--version work; malformed input exits 2 with every category failed. Outdated app names reach update-outdated-apps steps in report.json (D8).
- [x] 8. HTML report - gate: test_render.py: report.html renders all fixtures; scan.xss.json app name is escaped (autoescape on).
- [x] 9. PDF one-pager - gate: test_render.py: action-plan.pdf is exactly one page for every fixture.
- [x] 10. End-to-end + integrity - gate: test_fixtures.py and test_integrity.py pass; every report.json validates against report.schema.json; RPT-01..03, 06 hold.
- [ ] 11. PyInstaller - gate: engine.spec one-folder build runs --version and a fixture scan on a machine with no Python, in < 5 s.

Open judgement calls (spec gaps) and the solutions in code: docs/brick-a-decisions.md. Settle D1-D3 before phase 4.
