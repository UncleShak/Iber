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
| D1 | Per-fix severity | High | Before phase 4 | DECIDED 2026-10-28 (Tshedi) |
| D2 | "n things to tighten up" count | High | Before phase 4 | DECIDED 2026-10-28 (Tshedi) |
| D3 | Strict CategoryResult guards | Medium | Before phase 4 | DECIDED 2026-10-28 (Tshedi) |
| D4 | Error report summary and run_id | Medium | Phase 7 (CLI) | OPEN |
| D5 | generated_at uses the wall clock | Low | Phase 7 / s2.14 work | OPEN |
| D6 | Em dash written as an escape | Low | Any time | OPEN |
| D7 | Software rule evaluation order | High | Phase 5 | DECIDED 2026-10-28 (phase-5 prompt) |
| D8 | Run-specific fix steps | Medium | Phase 7 (CLI) | OPEN |
| D9 | R2 fix when System Restore is on | Low | Any time | OPEN |
| D10 | Healthy fixture scores software red | High | Phase 10 | CHANGED 2026-10-28 (Tshedi) |
| D11 | S7 amber has no fix (RPT-03) | Medium | Phase 10 | OPEN |

---

## D1. Per-fix severity

**Status.** DECIDED 2026-10-28 by Tshedi: keep the solution in code as is.

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

**Status.** DECIDED 2026-10-28 by Tshedi: keep the solution in code as is.

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

**Status.** DECIDED 2026-10-28 by Tshedi: keep the solution in code as is.

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

**Gap.** s0.8 shows "Not checked \u2014 needs admin" with an em dash;
CLAUDE.md requires ASCII-only files.

**Solution in code.** Source files use the escape `\u2014`, so the files
stay ASCII but report.json and the HTML still show a real em dash.
Files: `engine/antigravity_engine/scoring/result.py`,
`engine/tests/test_aggregator.py`.

**Why revisit.** Only if "ASCII only" is meant to cover engine output too,
or the PDF font lacks the glyph (check in phase 9).

**Alternatives.**
- Keep the escape (current).
- Use "Not checked - needs admin" everywhere.

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

**Gap.** s2.5.3 S7 (empty installed list) is amber with no fix id, but
RPT-03 (s7.6) requires every red/amber category to have a fix.

**Solution in code.** Follows s2.5.3: amber, no fix, one amber evidence
row. No current fixture has an empty list, so phase 10 won't trip on it.

**Alternatives.**
- Keep as is and exempt S7 in `test_integrity.py`.
- Add a catalogue fix such as "re-run the scan as administrator".

