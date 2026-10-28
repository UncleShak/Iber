# Brick A - open decisions log

Judgement calls made where docs/antigravity_manual_v1.1.md is silent or
ambiguous. Each entry records the gap, the solution currently in the code,
why it should be revisited, and the alternatives. None is a known bug: the
suite passes and every report validates against report.schema.json.

Status values: OPEN (needs an owner decision), DECIDED (keep as is, with date
and who decided), CHANGED (replaced; note the commit).

Logged: 2026-10-27, phase 3 (commit 8ef714d).

| ID | Topic | Priority | Decide by | Status |
|---|---|---|---|---|
| D1 | Per-fix severity | High | Before phase 4 | CHANGED 2026-10-28 (Tshedi) |
| D2 | "n things to tighten up" count | High | Before phase 4 | CHANGED 2026-10-28 (Tshedi) |
| D3 | Strict CategoryResult guards | Medium | Before phase 4 | CHANGED 2026-10-28 (Tshedi) |
| D4 | Error report summary and run_id | Medium | Phase 7 (CLI) | CHANGED 2026-10-28 (Tshedi) |
| D5 | generated_at uses the wall clock | Low | Phase 7 / s2.14 work | DECIDED 2026-10-28 (Tshedi) |
| D6 | Em dash written as an escape | Low | Any time | CHANGED 2026-10-28 (Tshedi) |
| D7 | Software rule evaluation order | High | Phase 5 | DECIDED 2026-10-28 (phase-5 prompt) |
| D8 | Run-specific fix steps | Medium | Phase 7 (CLI) | DECIDED 2026-10-28 (Tshedi) |
| D9 | R2 fix when System Restore is on | Low | Any time | CHANGED 2026-10-28 (Tshedi) |
| D10 | Healthy fixture scores software red | High | Phase 10 | CHANGED 2026-10-28 (Tshedi) |
| D11 | S7 amber has no fix (RPT-03) | Medium | Phase 10 | CHANGED 2026-10-28 (Tshedi) |
| D12 | BitLocker "still encrypting" has no fix (RPT-03) | Medium | Phase 10 | DECIDED 2026-10-28 (Tshedi) |
| D13 | When CFA/ASR are excluded; third-party AV always green | High | Phase 6 | DECIDED 2026-10-28 (Tshedi) |
| D14 | Null fields and all-grey protection category | Medium | Phase 6 | DECIDED 2026-10-28 (Tshedi) |
| D15 | All-null recovery section rated green | Medium | Any time | CHANGED 2026-10-28 (Tshedi) |
| D16 | Licence org in the HTML header | Low | Phase 10 / integration | OPEN |
| D17 | Failed protection sub-check shown as unavailable | High | Phase 10 | CHANGED 2026-10-28 (phase-10 RPT-01) |
| D18 | Backup B4/B5/B7 rows carried no status | High | Phase 10 | CHANGED 2026-10-28 (phase-10 RPT-02) |
| D19 | Evidence bundle gaps in s2.14 | Medium | Before RPT-11 | OPEN |

---

## D1. Per-fix severity

**Status.** CHANGED 2026-10-28 by Tshedi in commit 6a9e6c3 (first DECIDED as is the same day).
Each catalogue `Fix` now has `max_severity` taken from the s2.9 severity
column: amber-only fixes (encrypt-device-home, enable-tamper-protection,
enable-cfa, enable-asr-rules, run-backup-now, verify-backup-agent,
restart-to-finish-updates, plan-windows-11, create-restore-point, and
rescan-installed-apps from D11) are capped at amber in `resolve()`, whatever
the category status. `fix_severity` stays, now only for red-capable fixes
attached by an amber rule inside a red category (e.g.
update-defender-definitions at 4-7 days while BitLocker is off). The patch
scorer's own plan-windows-11 override was removed. Side effect: R2's
create-restore-point (D9) now ranks amber in report.json.
Files: `scoring/fixes.py` (`Fix.max_severity`, `resolve`), `scoring/patch.py`.
Tests: `test_catalogue_matches_spec_table`, `test_amber_only_fix_is_capped_*`,
`test_cap_without_fix_severity_keeps_cfa_out_of_top_three` (test_ranking.py).

**Gap.** s2.9 says a fix's severity is "the severity of the worst rule that
attached it". s0.8 gives a category only a `fix_ids` list, so the category
status is the only severity available downstream.

**Solution in code.** `CategoryResult` has an optional `fix_severity`
mapping (fix id -> red/amber). `CategoryResult.fix_pairs()` returns
`(fix_id, severity)` pairs, using the mapping when set and the category status
otherwise. `scoring.fixes.resolve()` consumes those pairs. The field is
internal and never written to report.json.
Files: `engine/antigravity_engine/scoring/result.py`
(`CategoryResult.fix_severity`, `fix_pairs`).

**Why revisit.** Without it, a red protection category (Defender off) that
also attaches `enable-cfa` would rank CFA as red, so it could push
`turn-on-file-history` out of the top 3. The cost is a field not in the
phase-3 prompt, and the phase 4-6 scorers must fill it whenever one category
attaches fixes of mixed severity.

**Alternatives.**
- Keep the field (current).
- Have scorers return a list of `(fix_id, severity)` directly instead of
  `fix_ids`, deriving `fix_ids` from it.
- Drop it and accept category status as fix severity (simpler, but ranks
  amber fixes inside red categories too high).

---

## D2. "n things to tighten up" count

**Status.** CHANGED 2026-10-28 by Tshedi in commit 6a9e6c3 (first DECIDED as is the same day).
n = number of amber fixes in the resolved `fixes[]`, so the headline matches
the fix cards; if no amber result attached a fix, n falls back to the number
of amber categories. `risk.summary(results, fixes)` now takes the resolved
fixes as a required argument; the phase 7 CLI must call `resolve()` first.
File: `engine/antigravity_engine/risk.py`. Tests: `test_summary_*`
(test_aggregator.py).

**Gap.** s2.6 summary row "No urgent issues, but {n} things to tighten up."
does not define n.

**Solution in code.** n = number of categories with status amber, with
singular/plural handled ("1 thing" / "2 things").
File: `engine/antigravity_engine/risk.py` (`summary`).

**Why revisit.** n could instead mean the number of amber fixes. These
differ: protection alone can attach three amber fixes while being one amber
category. It changes the headline the owner-manager reads first.

**Alternatives.**
- Count amber categories (current).
- Count amber fixes in `fixes[]` (would need `summary()` to take the
  resolved fixes as input).

---

## D3. Strict CategoryResult guards

**Status.** CHANGED 2026-10-28 by Tshedi in commit 6a9e6c3 (first DECIDED as is the same day).
Scan-driven limits now clip instead of raising: an explanation over 200
chars is cut with "...", evidence past 8 rows keeps the first 8, and a
`fix_steps` step over 160 chars is cut with "..." (it carries app names, D8).
Each clip emits a `ClippedWarning` (stderr at runtime). Logic guards still
raise: unknown category, unrated status built directly, empty explanation,
fixes on a green/unrated result, bad `fix_severity`, 0 or more than 5 steps,
an empty step. tests/conftest.py turns `ClippedWarning` into an error, so any
test that clips fails unless it expects the warning; test_integrity.py
checks no fixture clips in any existing scorer.
File: `engine/antigravity_engine/scoring/result.py`
(`ClippedWarning`, `CategoryResult._clip_scan_driven`).

**Gap.** s2.7 only requires that unavailable/failed come from the factory
methods. Other invariants are unstated in code terms.

**Solution in code.** `CategoryResult.__post_init__` also rejects:
- an unknown category id;
- an explanation that is empty or over 200 chars;
- more than 8 evidence rows;
- fixes attached to a green, unavailable or failed category;
- a `fix_severity` entry for an unattached fix, or one worse than the
  category status.
File: `engine/antigravity_engine/scoring/result.py`.

**Why revisit.** These turn scorer bugs into test-time crashes, which is
the intent. But s2.7 says an exception inside a scorer makes that category
`failed` at runtime. A guard stricter than the spec intends would show a
valid finding as "Check failed". The 200-char and 8-row limits match
report.schema.json, so the realistic risk is small.

**Alternatives.**
- Keep all guards (current).
- Keep only the schema-backed limits and the unrated-construction guard;
  move the rest into tests (e.g. test_integrity.py).
- Clip over-long explanations and evidence instead of raising.

---

## D4. Error report summary and run_id

**Status.** CHANGED 2026-10-28 by Tshedi. The app's run folder name always
equals its runId, but scan.json's run_id matches it only when the app
launched the collector with -RunId. So:
- new `--run-id ID`: the error report (exit 2) uses it as run_id; an invalid
  ID is ignored with a stderr warning and the `_0000` fallback stays;
- a valid scan keeps its own run_id in report.json and evidence.json even if
  --run-id differs (stderr warning only), because --verify recomputes the
  report from the embedded scan alone;
- the error summary is the fixed "We couldn't read the scan results."; the
  parser detail goes to stderr only.
Files: `engine/antigravity_engine/__main__.py`, `report_model.py`.
Tests: `test_run_id_*`, `test_invalid_run_id_is_ignored_with_warning`,
`test_valid_scan_keeps_its_own_run_id_and_warns_on_mismatch`,
`test_mismatched_run_id_bundle_still_verifies` (test_cli.py);
`test_error_report*` (test_aggregator.py).

The original entry follows.

**Gap.** s2.4 step 4 says the error text goes in `summary`; the exact
wording and what to do when the input has no usable run_id are unstated.

**Solution in code.** `build_error_report()`:
- summary = "We couldn't read the scan results: <error>", clipped to 200
  chars with "...";
- run_id = the caller's run_id if it matches the schema pattern, otherwise
  generated_at formatted as `YYYY-MM-DDTHH-MM-SSZ_0000`;
- each category explanation = "This check couldn't run because the scan
  results couldn't be read."
File: `engine/antigravity_engine/report_model.py`.

**Why revisit.** The CLI (phase 7) does not exist yet. A synthesised
`_0000` run_id may not match how Brick C (Frank) and Brick D (Schwan) locate
run folders, and parser error text (e.g. "not valid JSON: Expecting value at
line 1 column 1") is technical for an owner-manager.

**Alternatives.**
- Have the CLI always pass the run_id it was launched with (the app knows
  it from the run folder name).
- Use a fixed plain-English summary and put the raw error only on stderr.

---

## D5. generated_at uses the wall clock

**Status.** DECIDED 2026-10-28 by Tshedi: keep the wall clock. --verify
ignores generated_at (s2.14.2 step 4), and a new Evidence ID per run tells
two reports of the same scan apart. Tests and fixture regeneration that need
fixed output pass generated_at or ignore it.

**Gap.** s2.3 says "now" is always `collected_at`, never the wall clock.
`generated_at` in s0.8 is the time the report was produced.

**Solution in code.** `generated_at` defaults to the current UTC time;
callers and tests may pass a fixed `generated_at`.
File: `engine/antigravity_engine/report_model.py` (`_timestamp`).

**Why revisit.** If the evidence bundle (s2.14) or fixture regeneration
(s2.11 step 5) needs byte-identical report.json for the same scan, a
wall-clock timestamp breaks that.

**Alternatives.**
- Keep the wall clock (current); make tests and fixture regeneration pass
  a fixed time.
- Use `collected_at` as `generated_at` (fully deterministic, but no longer
  "when the report was generated").

---

## D6. Em dash written as an escape

**Status.** CHANGED 2026-10-28 by Tshedi: report.json is written with
`ensure_ascii=True` once committed report fixtures made it a repo file.

**Gap.** s0.8 shows "Not checked \u2014 needs admin" with an em dash;
CLAUDE.md requires ASCII-only files.

**Solution in code.** Source files use the escape `\u2014`. report.json is
written with `ensure_ascii=True`, so the file on disk (and every
shared/fixtures/report.*.json) is ASCII with `\u2014` escapes, while any
JSON reader gets the same em dash text as s0.8. report.html still holds a
real em dash; it goes to out/, which is not committed.
Files: `engine/antigravity_engine/scoring/result.py`,
`engine/antigravity_engine/__main__.py` (`write_json`).
Tests: `test_report_json_is_ascii_but_keeps_the_em_dash` (test_cli.py).

**Alternatives.**
- Write raw UTF-8 and read "ASCII only" as source files only (previous).
- Use "Not checked - needs admin" everywhere (changes user-visible text
  away from s0.8).

---

## D7. Software rule evaluation order

Logged: 2026-10-28, phase 5.

**Status.** DECIDED 2026-10-28: ordering set by the phase-5 prompt.

**Gap.** s2.5.3 lists S1-S7 "first match wins", but S5 ("all matched apps
at or above min") is vacuously true when nothing matched, so S6 and S7 could
never fire if the table were read top to bottom.

**Solution in code.** Evaluated S1, S7, S6, S2, S3, S4, S5. An empty list
(S7) is amber before anything else; zero matches (S6) is green with "None of
your N apps are on our watch list" before the version rules.
File: `engine/antigravity_engine/scoring/software.py` (`score`).
Test: `test_s6_is_checked_before_s5`.

---

## D8. Run-specific fix steps

Logged: 2026-10-28, phase 5.

**Status.** DECIDED 2026-10-28 by Tshedi: keep `fix_steps`. Phase 7 must add
an end-to-end test that an outdated app's name appears in the
`update-outdated-apps` steps in report.json, so a missed hand-off to
`resolve()` fails a test instead of silently falling back to catalogue text.
Noted on the phase 7 gate in PLAN.md.

**Gap.** s2.5.3 says the `update-outdated-apps` steps list the outdated app
names, but s2.9 fixes are a static catalogue and `resolve()` copied its steps.

**Solution in code.** `CategoryResult.fix_steps` (internal, never written to
report.json) maps a fix id to steps for this run; guarded to 1-5 items of
1-160 chars (report.schema.json). `fixes.resolve(pairs, steps)` uses them
in place of the catalogue steps. Software fills it: step 1 names up to 4
apps then "and N more"; eol apps get an extra "Uninstall ..." step.
Files: `scoring/result.py`, `scoring/fixes.py`, `scoring/software.py`.

**Why revisit.** The CLI (phase 7) must merge `fix_steps` from all results
and pass it to `resolve()`, or the named steps are lost. If two categories
ever supplied steps for the same fix id, a merge rule would be needed.

**Alternatives.**
- Keep the field (current).
- Put the app names in the evidence only and keep catalogue steps static.

---

## D9. R2 fix when System Restore is on

Logged: 2026-10-28, phase 5.

**Status.** CHANGED 2026-10-28 by Tshedi: when `system_restore_enabled` is
true, R2 attaches `enable-winre` and `create-restore-point`; when it is false
or unknown, `enable-winre` and `turn-on-system-restore` as in s2.5.5. The
category stays red either way. Tests: `test_r2_*` in test_recovery.py.

**Gap.** s2.5.5 R2 fires on WinRE off and (System Restore off **or** no
restore points) and always attaches `turn-on-system-restore`. When System
Restore is on but has no points, "Turn on System Restore" is not quite the
right advice.

**Solution in code.** Follows the table literally: R2 attaches
`enable-winre` and `turn-on-system-restore` in both cases. The catalogue
steps are harmless when it is already on.
File: `engine/antigravity_engine/scoring/recovery.py`.

**Alternatives.**
- Keep as is (current).
- Attach `create-restore-point` instead when `system_restore_enabled` is
  true.

---

## D10. Healthy fixture scores software red

Logged: 2026-10-28, phase 5.

**Status.** CHANGED 2026-10-28 by Tshedi: option 1, fixture versions bumped.
healthy, home-edition, no-bitlocker and xss now carry each app at exactly its
baseline `min_safe_version` (Chrome 142.0.7444.175, Acrobat Reader
25.001.20937, 7-Zip 25.00), so software scores green. defender-off keeps
Chrome 118.0.5993.118 (deliberately outdated). The s0.7 examples in the
manual still show the old versions. If the baseline minimums are raised,
these fixtures must be bumped again.

**Gap.** s0.7 says `scan.healthy.json` is "all green", but its apps
(Chrome 131.0.6778.86, Acrobat Reader 24.4.20220, 7-Zip 24.08) are below
the phase-2 baseline minimums (142.0.7444.175, 25.001.20937, 25.00), so
software is red. The same holds for the home-edition, no-bitlocker and xss
fixtures. Phase 10 `test_fixtures.py` checks the expected RAG.

**Solution in code.** None yet: the scorer is correct for the data. Phase-5
tests build their own app lists instead of relying on the healthy fixture.

**Why revisit.** Must be settled before phase 10. Fixtures are owned
outside Brick A (CLAUDE.md: don't edit shared/fixtures unasked).

**Alternatives.**
- Update the fixtures' app versions to current ones (needs fixture owner
  and the user's go-ahead).
- Treat the expected-RAG note as covering only the category each fixture
  is about, and assert software separately.

---

## D11. S7 amber has no fix (RPT-03)

Logged: 2026-10-28, phase 5.

**Status.** CHANGED 2026-10-28 by Tshedi: option "add a catalogue fix". New
fix `rescan-installed-apps` (software, amber, 5 min, no admin: restart, scan
again, ask IT helper if still empty) is attached by S7. It is an addition
beyond the s2.9 table; `test_ranking.py` SPEC_TABLE lists it.

**Gap.** s2.5.3 S7 (empty installed list) is amber with no fix id, but
RPT-03 (s7.6) requires every red/amber category to have a fix.

**Solution in code.** Follows s2.5.3: amber, no fix, one amber evidence
row. No current fixture has an empty list, so phase 10 won't trip on it.

**Alternatives.**
- Keep as is and exempt S7 in `test_integrity.py`.
- Add a catalogue fix such as "re-run the scan as administrator".

---

## D12. BitLocker "still encrypting" has no fix (RPT-03)

Logged: 2026-10-28, phase 6.

**Status.** DECIDED 2026-10-28 by Tshedi: keep the catalogue fix (D11 precedent).

**Gap.** s2.5.4 rates `os_volume_protection == "on"` with
`os_volume_encryption_pct < 100` amber with no fix id ("still encrypting;
leave the PC on"). If that is the only finding, the category is amber with
no fix, which breaks RPT-03 (s7.6) - the same conflict as D11.

**Solution in code.** New fix `finish-bitlocker-encryption` (protection,
amber cap, 5 min, no admin: keep the PC on and plugged in, watch progress in
Manage BitLocker, scan again). Attached only by the encrypting row.
Files: `scoring/fixes.py`, `scoring/protection.py`; `test_ranking.py`
SPEC_TABLE lists it.
Test: `test_bitlocker_still_encrypting_is_amber_with_finish_fix`.

**Alternatives.**
- Keep the fix (current).
- Follow s2.5.4 literally (amber, no fix) and exempt it in `test_integrity.py`.
- Rate the encrypting row green with an explanatory value (no RPT-03 issue,
  but hides a real, temporary exposure).

---

## D13. When CFA/ASR are excluded; third-party AV always green

Logged: 2026-10-28, phase 6.

**Status.** DECIDED 2026-10-28 by Tshedi: keep as built.

**Gap.** s2.5.4 says "If Defender is off, the ASR and CFA rows ... are
excluded from rating" without defining "off". Its Defender table only greens
a third-party AV when `antivirus_enabled == false`, but s3.6 says a passive
Defender (third-party AV present) is "Not penalised" and its CFA/ASR are
"Excluded from rating" whenever `third_party_av` is set. A passive Defender
can report `antivirus_enabled: true` with real-time off and stale
signatures, which the literal table would rate red.

**Solution in code.** (1) `third_party_av` set -> Defender row green
"Protected by <name>", checked before every other Defender condition.
(2) CFA and ASR are excluded (neutral row "Only works when Microsoft
Defender is your antivirus", no status, no fix) when the Defender section is
ok and any of: `third_party_av` set, `antivirus_enabled` false,
`realtime_enabled` false. Both features need Defender real-time protection
to act. If the Defender section itself is unavailable/failed, CFA/ASR are
rated normally (they are read separately, s3.5).
Tests: `test_third_party_av_wins_over_stale_signatures_and_tamper_off`,
`test_cfa_and_asr_excluded_when_defender_not_primary`,
`test_defender_section_failed_is_grey_and_cfa_asr_still_rated`.

**Alternatives.**
- Exclude only on `antivirus_enabled` false / `third_party_av` set, so a
  real-time-off PC also gets CFA/ASR fixes (more fixes, red Defender row
  already covers it).
- Apply the Defender table literally and only use `third_party_av` when
  `antivirus_enabled` is false.

---

## D14. Null fields and all-grey protection category

Logged: 2026-10-28, phase 6.

**Status.** DECIDED 2026-10-28 by Tshedi: keep as built.

**Gap.** s2.5.4 covers section `unavailable`/`failed` but not null fields
inside an `ok` section, nor a category where no sub-check can be rated.

**Solution in code.** Conditions only fire on known values; a null never
makes a row worse (same rule as recovery, s2.5.5). A row with no rule fired
and its deciding field null is grey ("Not checked", or "Not checked - needs
admin" when not elevated): Defender when `antivirus_enabled` or
`realtime_enabled` is null, BitLocker when `os_volume_protection` is null,
CFA when `mode` is null. A green category with grey rows reads "The
protections we could check are all on." plus "Run as administrator for a
full check." when not elevated. If no row is rated: `failed` when all four
sections failed, else `unavailable` with the four grey rows as evidence.
Tests: `test_defender_null_running_state_is_grey_not_red`,
`test_bitlocker_ok_with_null_protection_is_grey`,
`test_all_sections_unavailable_is_unavailable_with_grey_rows`,
`test_all_sections_failed_is_failed`.

**Alternatives.**
- Treat an all-grey category as green with the admin sentence (like R7).
- Treat null `antivirus_enabled` as off (red) - rejected: penalises a
  collector gap.

---

## D15. All-null recovery section rated green

Logged: 2026-10-28, scoring review.

**Status.** CHANGED 2026-10-28 by Tshedi: option 2. When `winre_enabled`,
`system_restore_enabled`, `restore_point_count` and `latest_restore_point`
are all null in an ok section, recovery is `unavailable` with the four grey
rows as evidence (same rule as D14 for protection). The explanation is the
admin sentence when the scan was not elevated, else "This couldn't be
checked on this PC." Any mix with at least one known field is unchanged:
green with grey rows when R2-R5 don't fire.
File: `engine/antigravity_engine/scoring/recovery.py` (`score`).
Tests: `test_all_null_non_admin_is_unavailable_with_grey_rows`,
`test_all_null_elevated_is_unavailable_without_admin_sentence`,
`test_one_known_field_keeps_null_mix_green`,
`test_points_counted_but_newest_date_null_is_grey_and_green`
(test_recovery.py).

**Gap.** s2.5.5 R7 covers only `winre_enabled` and `restore_point_count`
null with `system_restore_enabled == true`. Other null mixes are unstated.

**Solution in code (before).** Any null mix that R2-R5 left unrated was
green with grey rows, including every field null: a green tile with no
evidence behind it. A green category also counts toward the risk score
(weight 10, 0 points), which can lower the headline to "good shape";
`unavailable` is removed from both sides of the s2.6 formula.

**Alternatives.**
- Keep green with grey rows for every null mix.
- Unavailable only when nothing is known (chosen).
- Follow R7 literally: green only when `system_restore_enabled == true`,
  unavailable for every other unrated null mix.

---

## D16. Licence org in the HTML header

Logged: 2026-10-28, phase 8.

**Gap.** s4.10 puts "licence org" in the report.html header, but s2.3 row 9
says renderers read only the report model, and report.json (s0.8) has no
org field. The licence token is verified by the app (s3.11, s4.9.3 footer),
not the engine.

**Solution in code.** `render.html.render(report, path, org=None)` takes the
org as an optional argument; the header shows "Licensed to {org}" only when
it is given. The CLI does not pass it, so engine-made reports omit the line.
Also added: `python -m antigravity_engine.render.html report.json
report.html`, which validates report.json against report.schema.json and
renders it (re-render without re-scoring).
File: `engine/antigravity_engine/render/html.py`.
Tests: `test_licence_org_only_when_given`, `test_main_*` (test_render.py).

**Why revisit.** As shipped, no report.html carries the org, which s4.10
asks for.

**Alternatives.**
- Add a CLI flag `--org` that the app passes when it spawns the engine
  (no contract change; engine still never reads the token).
- Add an optional `org` to report.schema.json (contract change, s0.10).
- Drop org from the HTML; the app footer already shows it.

---

## D17. Failed protection sub-check shown as unavailable

Logged: 2026-10-28, phase 10.

**Status.** CHANGED 2026-10-28 in the phase-10 commit; found by
test_integrity.py (RPT-01).

**Gap.** s2.5.4 says unavailable/failed sub-checks "appear as grey rows" but
not with which status. The scorer gave both the status `unavailable`, so a
Defender probe that threw read "Not checked" instead of "Check failed". That
breaks RPT-01 and s0.9 rule 2 ("missing probes appear as evidence rows with
that status"); s3 shows a throwing Defender probe as grey-striped.

**Solution in code.** A failed sub-check section gives a `failed` row whose
value is the collector error (rendered "Couldn't read: <error>"); an
unavailable one keeps the `unavailable` row. Both are still skipped for
rating, and a failed row counts as grey for the "could check" explanation.
File: `engine/antigravity_engine/scoring/protection.py` (`_grey_section`).
Tests: `test_defender_section_failed_is_grey_and_cfa_asr_still_rated`,
`test_bitlocker_failed_on_home_is_grey_not_rated`,
`test_status_mapping_protection_rows` (test_integrity.py).

---

## D18. Backup B4/B5/B7 rows carried no status

Logged: 2026-10-28, phase 10.

**Status.** CHANGED 2026-10-28 in the phase-10 commit; found by
test_integrity.py (RPT-02) on scan.defender-off.json.

**Gap.** B4, B5 and B7 rate the category amber/red from the absence of a
dated backup, but every row they show (File History off, OneDrive sync,
backup programs) had no status, so no evidence row matched the category
status (RPT-02).

**Solution in code.** The deciding rows take the category status: B4 the
"Backup programs found" row (amber); B5 the OneDrive and/or shadow-copy row
that triggered it (amber); B7 every row without a status, since each one is
a missing kind of backup (red). Grey rows stay grey.
File: `engine/antigravity_engine/scoring/backup.py` (`_mark`).
Tests: `test_b4_agent_row_is_amber`, `test_b5_only_the_deciding_rows_are_amber`,
`test_b7_every_nothing_found_row_is_red`, `test_b7_keeps_grey_rows_grey`.

**Alternatives.**
- B7: mark only the File History row red (the fix target).

---

## D19. Evidence bundle gaps in s2.14

Logged: 2026-10-28, phase 12.

**Status.** OPEN. Each point below is what the code does now.

**1. Baseline hash.** s2.14.1 says "hash of the exact baseline file used".
Raw bytes differ between an LF checkout (macOS) and a CRLF one (Windows,
core.autocrlf true), so the same baseline would give CANNOT_VERIFY across
machines. `baseline_sha256` is the canonical hash of the parsed baseline
JSON instead: same content, same hash.
Test: `test_baseline_hash_ignores_line_endings`.

**2. No bundle on bad input.** s2.13 says evidence.json "for every run". A
scan that fails the contract (exit 2) may not even be JSON, and its error
report is not derived from the scan, so there is nothing to recompute.
evidence.json is written for every scored run (exit 0 and 3, and
--json-only), never for exit 2. Test: `test_bad_input_writes_no_evidence`.

**3. Evidence ID check.** s2.14.2 step 2 checks only the two hashes. The
verifier also rejects an `evidence_id` that does not match
`report_sha256` (TAMPERED: evidence ID edited), so the ID on paper always
names the report that verified. Test: `test_edited_evidence_id_is_tampered`.

**4. Patch releases.** Step 4 ignores only `generated_at`, but report.json
carries `engine_version`, so a 0.1.1 verifier would call every 0.1.0 bundle
TAMPERED although step 3 accepts the same major.minor. When major.minor
match, step 4 also ignores the patch part of the report's engine_version.
Test: `test_patch_release_of_same_minor_still_verifies`.

**5. Schema location.** CHANGED 2026-10-28 when main was merged in:
step 1 now validates against shared/contract/evidence.schema.json (Brick B,
identical to A.3), bundled under contract/ by engine.spec. The inline copy
is gone.

**6. Edits that cannot change the report.** Flipping a scan field that does
not affect any rating (realtime_enabled when antivirus is already off) and
recomputing the hashes still VERIFIES: the report really is what the rules
give for that scan. This is the s2.14 honest scope (the verifier does not
prove the scan is genuine), so the s2.14.4 "scan field changed" case is
tested on the healthy scan, where the edit changes the result.
Tests: `test_scan_edit_with_rehash_does_not_match_report`,
`test_scan_edit_that_cannot_change_the_report_still_verifies`.

**7. "Not checked: n items"** counts evidence rows whose status is
unavailable or failed.

**Alternatives.**
- 1: hash raw bytes and add a .gitattributes rule pinning baseline/*.json to LF.
- 2: write a bundle with the raw input bytes hashed but no report check.
