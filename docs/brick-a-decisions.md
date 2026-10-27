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
| D1 | Per-fix severity | High | Before phase 4 | OPEN |
| D2 | "n things to tighten up" count | High | Before phase 4 | OPEN |
| D3 | Strict CategoryResult guards | Medium | Before phase 4 | OPEN |
| D4 | Error report summary and run_id | Medium | Phase 7 (CLI) | OPEN |
| D5 | generated_at uses the wall clock | Low | Phase 7 / s2.14 work | OPEN |
| D6 | Em dash written as an escape | Low | Any time | OPEN |

---

## D1. Per-fix severity

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
