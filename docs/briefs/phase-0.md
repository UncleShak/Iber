# Phase 0 brief: Contract

Branch `contract/initial-schema` · 27 Oct 2026 · manual §0.5–§0.7, §0.10, Appendix A.1, A.3

## 1. What was built

The "contract" is the agreed shape of the data passed between the four parts of the product.

| File | What it does and why |
|---|---|
| `shared/contract/scan.schema.json` | Rules for what a valid `scan.json` (collector output) must look like. A *JSON Schema* is a machine-readable rule set a validator can check a file against. This file is copied character-for-character from manual Appendix A.1. |
| `shared/contract/evidence.schema.json` | Rules for `evidence.json`, the bundle an insurer checks with `engine.exe --verify`. Copied from Appendix A.3. |
| `shared/contract/types.ts` | The same shapes written as TypeScript types, so the UI and licence code get compile errors when they misuse a field. It is hand-written, because a generator would be a new dependency. It covers the scan and evidence files only; report types are Tshedi's (A.2). |
| `shared/contract/CHANGELOG.md` | Version 1.0.0 entry, the decisions below, and a sign-off table for Shakir and Tshedi (§0.10 step 3). |
| `shared/fixtures/scan.healthy.json`, `scan.no-bitlocker.json`, `scan.defender-off.json` | The three example scans from §0.7, copied exactly. Bricks A and C test against these instead of a real PC (§0.2). |
| `shared/fixtures/scan.home-edition.json` | The healthy scan changed to Windows 11 Home: edition `Core`, BitLocker `unavailable` with the §0.7 error text. Still run as admin, so "unavailable" is clearly caused by Home and not by missing rights. |
| `shared/fixtures/scan.xss.json` | The healthy scan with the RPT-07 attack string `<script>alert(1)</script><img src=x onerror=alert(2)>` planted in every place the report actually displays text. *XSS* (cross-site scripting) means text that a web page runs as code by mistake. |
| `shared/contract/tests/test_contract.py` | 96 automated checks (pytest) of schemas, fixtures and types. |
| `shared/contract/tests/types.check.ts`, `tests/tsconfig.json` | A file that is only type-checked, never run. Correct objects must compile and 7 deliberately wrong ones must not. |

## 2. How it works

1. The two schemas were pulled out of the manual's own code blocks by a short script, so nothing was retyped by hand. Socrates confirmed both equal the manual exactly.
2. Fixtures 1–3 were pulled out of §0.7 the same way. Home-edition and xss were built from healthy by changing only the listed fields.
3. pytest loads each schema and fixture. It rejects empty files and files with a *BOM* (an invisible marker at the start of a file, forbidden by §0.5). It then validates with the `jsonschema` library already installed in the engine's `.venv`.
4. A drift check reads `types.ts` as text and compares every interface with the schema: field names, which fields are optional, which accept `null`, and every allowed enum value. If someone later edits one file but not the other, this test fails.
5. `tsc` (the TypeScript compiler already in `desktop/node_modules`) checks `types.check.ts` with `--noEmit`, which means it writes no output files.

Safety: nothing here touches the system. The only files written are the ones listed above. There are no registry reads, cmdlets, network calls or crypto operations. Hashes in fixtures are dummy values. No new dependencies were added.

## 3. Tests written

| Test | What it checks | Why it matters |
|---|---|---|
| `test_schema_is_valid_draft_2020_12` ×2 | Each schema is itself a valid draft 2020-12 schema | A broken schema would silently accept everything |
| `test_fixture_validates_against_scan_schema` ×5 | Every fixture passes the schema | Bricks A and C build on these fixtures |
| `test_fixture_keys_match_manual_table` ×5 | Fixtures hold exactly the §0.6 keys, required ones present | Automated version of PRV-05 (no extra data collected) |
| `test_schema_properties_match_manual_table` ×14 | Schema fields and required lists equal §0.6, section by section | Catches the schema drifting from the manual |
| `test_schema_rejects_bad_input` ×19 | Rejects: major version 2, raw hostname, bad run_id, `status:"error"`, OneDrive "Downloads", 11 hotfixes, a missing key, ASR "enabled", 101 %, error text over 200 characters, `+02:00` time, `/Date()/` time, `null` in place of 5 lists, a single object in place of a list ×2 | The last 9 are the usual PowerShell 5.1 JSON mistakes (§3.8), so the Phase 1 collector gets caught |
| `test_healthy/no_bitlocker/home_edition/defender_off_fixture` | Each fixture holds what its name promises | A fixture that drifts would mislead the engine's tests |
| `test_xss_fixture_carries_rpt07_payload` | Attack string is in `os_caption`, `third_party_agents`, `third_party_av` (AV off) and one app name | Unmatched apps are never rendered (§2.5.3), so the string must sit where text is displayed (§2.5.4 "Protected by …") |
| `test_fixture_has_no_personal_data` ×5 | No IPv4, MAC, Windows path, user folder, email, `DESKTOP-xxxx` name or `%VAR%` | POPIA (§0.5) |
| `test_run_ids_unique_and_match_collected_at` | run_ids unique; timestamp equals `collected_at` | Run folders must not collide |
| `test_patch_fields_consistent` ×5 | Count ≥ list length; latest date = newest hotfix; days = collected − latest | Locks in the arithmetic the engine re-checks |
| `test_evidence_schema_*` ×6 | Required keys equal A.3; a valid bundle passes; bad ID, version 2, missing `sha256:` prefix and missing ID are rejected | Guards the insurer verification file |
| `test_types_ts_matches_schema` ×14, `..._nullability_and_enums_...` ×14, `..._evidence_bundle_...` | `types.ts` matches the schema on keys, optionality, null and enums | Stops the UI's types silently disagreeing with the data |
| `tsc` on `types.check.ts` | Valid objects compile; 7 wrong ones (bad status, bad enums, missing key, wrong type) fail | Proves the types actually block mistakes |

## 4. Test results

**Tests first (red).** Every file was still empty. 68 failed, each for the right reason:
```
68 failed in 0.55s
test_contract.py:59: AssertionError: scan.schema.json is empty (not written yet)
test_contract.py:58: AssertionError: evidence.schema.json does not exist
types.check.ts(14,8): error TS2306: File '.../shared/contract/types.ts' is not a module.
```
Grouped by reason: scan.schema empty ×20, scan.healthy empty ×18, types.ts empty ×15, evidence.schema missing ×3, each other fixture empty ×3.

**After Socrates' review**, the new tests were run first against the existing files:
```
test_contract.py:247: AssertionError: assert 'Microsoft Windows 11 Pro' == '<script>aler...ror=alert(2)>'
1 failed, 95 passed
```
Mutation proof: I temporarily broke `types.ts` (made `shadow_copy_count` non-nullable, dropped `'warn'` and `'audit'`). The drift test failed on all three, and the file was then restored byte-for-byte:
```
BackupSection.shadow_copy_count: TS 'number' vs schema {'type': ['integer', 'null'], 'minimum': 0}
CfaSection.mode: TS 'CfaMode | null' vs schema {'enum': ['enabled', 'disabled', 'audit', None]}
AsrRule.action: TS 'AsrAction' vs schema {'enum': ['block', 'audit', 'warn', 'off']}
```
**Final gate (green):**
```
96 passed in 0.72s
tsc exit 0
```
There are no earlier phases, and `Test-ReadOnly.ps1` only applies from Phase 2 onward.

## 5. Run it yourself

Working folder for both commands: `C:\Users\HP\antigravity`

```powershell
engine\.venv\Scripts\python -B -m pytest -q -p no:cacheprovider shared\contract\tests
```
Expect `96 passed`. A failure names the file and field. "is empty" or "does not exist" means a contract file is missing.

```powershell
desktop\node_modules\.bin\tsc -p shared\contract\tests\tsconfig.json
```
Expect no output (exit 0). `Unused '@ts-expect-error'` means a type became too loose. Any other error means `types.ts` and the sample objects disagree.

## 6. Decisions and limits

- **`report.schema.json` was left empty for Tshedi** (your call). `EvidenceBundle.report` is typed loosely until A.2 lands.
- **Manual corrected** (authorised by Shakir; same PR, per §0.10 step 5). Five text edits in `docs/antigravity_manual_v1.1.md`:
  1. §0.6 line 355: `hotfix_count` type is now `integer|null`, matching A.1. Tshedi's `contract.py` must allow null.
  2. §0.5 line 245: `duration_ms` comment now says "collector target < 60000 (not enforced by the schema)".
  3. §0.5 line 233 and Appendix C line 4638: `types.ts` described as hand-written and drift-tested (scan + evidence only).
  4. §0.7 line 408: Fixture 2 described as "same ratings as Fixture 1 except BitLocker; other fields are shortened sample values".
- **Schema gaps, copied as-is from A.1.** Raise these before the 16:00 freeze if you want them fixed:
  - `days_since_latest_hotfix` has no minimum, so a wrong clock gives a negative value that passes.
  - `hostname_hash` accepts any length (`sha256:1` passes); the fixtures rely on short dummy hashes.
  - Date patterns accept impossible dates like month 13.
  - The evidence schema accepts any object for `scan`, and its `run_id` isn't linked to `scan.run_id`. `types.ts` promises more than the schema guarantees, so the verifier must not trust it.
- **POPIA regex limits:** it doesn't catch IPv6, MACs without separators, or arbitrary usernames. The IPv4 check could falsely flag a version like "7.1.2.3".
- **The drift check's parser is simple:** a single `extends`, no generics, no `/* */` comments inside interfaces. It is fine for today's file.
- **xss fixture choice:** `realtime_enabled` stays `true`, so the Defender row takes the "Protected by <third_party_av>" path (§2.5.4) and the string is rendered.
- **Found, not mine to change:**
  - `CLAUDE.md` is *tracked* in git (commit 00bdc2f), so your `.gitignore` entry doesn't hide it, and it is in the team repo.
  - Your uncommitted `CLAUDE.md` and `.gitignore` edits will not be staged in this contract commit.
  - There is no `.gitattributes` yet (Schwan, Appendix C), so git warns about LF→CRLF line endings on the JSON files.
- **Sign-off:** §0.10 needs Shakir and Tshedi to agree before the 16:00 Day 1 freeze. The CHANGELOG table is blank for you to fill in.

## 7. Pitch line

Every brick is tested against one shared, machine-checked contract, including a planted attack string, so a malicious app name on a client's PC can never run in their report.
