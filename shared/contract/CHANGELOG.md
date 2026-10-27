# Contract changelog

Versions of `scan.schema.json` (`schema_version`) and `evidence.schema.json` (`evidence_version`).
Change procedure: manual §0.10. Frozen after 16:00 Day 1; later changes need all four members' "agree".

## 1.0.0 — 2026-10-27

- `scan.schema.json`: initial version, verbatim from manual v1.1 Appendix A.1.
- `evidence.schema.json`: initial version, verbatim from manual v1.1 Appendix A.3.
- `types.ts`: hand-written TS mirror of both schemas (no generator dependency); checked by `tests/`.
- Fixtures: `scan.healthy`, `scan.no-bitlocker`, `scan.defender-off` (verbatim §0.7),
  `scan.home-edition` (§0.7 variant), `scan.xss` (RPT-07 payload, §7.6).
- `report.schema.json` (A.2): not included; owned by Brick A (Tshedi).

Decisions (manual v1.1 text corrected in the same PR: §0.5, §0.6, §0.7, Appendix C):
- `patch.hotfix_count` may be `null` (A.1); §0.6 now says `integer|null`. Python mirrors
  (`contract.py`) must allow null.
- `duration_ms < 60000` is a collector target, not a schema rule; §0.5 comment now says so.
- `types.ts` is hand-written, with a drift test (keys, optionality, nullability, enum values) in
  `tests/test_contract.py`; §0.5 and Appendix C now say so.
- §0.7 Fixture 2 description corrected: it also differs from Fixture 1 in sample values.
- `scan.xss.json` carries the RPT-07 payload in `host.os_caption`, `backup.third_party_agents`,
  `protection.defender.third_party_av` (with `antivirus_enabled: false`, so §2.5.4 renders
  "Protected by …") and one `software.installed` entry, since unmatched apps are never rendered (§2.5.3).

### Sign-off (§0.10 step 3)

| Who | Role | Agreed (date/time) |
|---|---|---|
| Shakir | Contract owner (B) | |
| Tshedi | Lead (A) | |
