# Phase 7 brief: integration (`-RunId`, `AG-PHASE:` markers, `contract-check.ps1`)

Branch `brick/collector`. Manual §3.3, §4.8, §5.8, §6.3 step 2.8. Before this phase, `origin/main` (engine, baseline, fixture update) was merged in as `d537a69`, keeping the corrected manual and Brick B `CLAUDE.md`. Not committed yet; waiting for `Verified`.

## 1. What was built

| File | What it does and why |
|---|---|
| `collector/collector.ps1` | `-RunId` and `-Only` are now checked by our own code instead of PowerShell's `ValidatePattern`/`ValidateSet` attributes (these reject a value while PowerShell is still reading the arguments, before our script runs, so the exit code was 1). A bad value now exits **64** ("bad arguments", §3.3) with fixed text `Bad -RunId` / `Bad -Only value`. The `-RunId` check is now strict: lower-case hex only, ASCII digits only, and no trailing newline. The old check was case-insensitive and let `…Z_ABCD` through, which the schema then rejects. `-RunId` (§3.3) and the `AG-PHASE:` markers (§4.8) were already built in Phase 1; this phase adds the missing tests. |
| `installer/contract-check.ps1` | Was an empty file. Now it is the end-to-end schema gate from §5.8 / §6.3 step 2.8. It runs the collector with `-DryRun`, checks `scan.json` with `validate.py`, runs the engine with `--json-only`, checks `report.json`, and prints `CONTRACT OK` (exit 0). If any step fails, it prints `CONTRACT BROKEN at <step>` (exit 1). `-ScanFile <file>` checks a given scan instead of running the collector, and `-Python <exe>` swaps the engine Python (both used by tests). |
| `collector/tests/Test-Integration.ps1` | 11 tests for the above. |

## 2. How it works

`collector.ps1` (unchanged except the argument checks):
1. Checks `-RunId` against `^[0-9]{4}-…Z_[0-9a-f]{4}\z`, case-sensitive (`\z` = true end of text). It also checks each `-Only` name against the six probe names. Any mismatch: fixed message on stderr, exit 64, before any probe or mock is loaded. Nothing is read or written.
2. If `-RunId` is given, it becomes `run_id`, so the run folder the app creates matches `scan.json` (§5.6 step 8).
3. With `-OutputPath`, one `AG-PHASE:<section>` line goes to stdout before each probe. These are the app's progress signal (§4.8). With `-DryRun` there are none, because stdout is the JSON there.

`contract-check.ps1` (a build tool, not shipped; reads this PC only through the read-only collector):
1. **Setup.** Confirms `engine\.venv\Scripts\python.exe`, `engine\tools\validate.py` and `baseline\software-baseline.json` exist. Creates `out\contract-check\` (git-ignored) and deletes any old `report.json` / `evidence.json` there, so a previous run can never make it pass. Uses .NET file calls, not `New-*`/`Remove-*` cmdlets.
2. **Collector.** `powershell.exe -NoProfile -File collector\collector.ps1 -DryRun` reads this PC (all reads, §3.7) and prints JSON. The script saves that JSON as UTF-8 without BOM (byte-order mark: a hidden 3-byte prefix that breaks JSON parsers).
3. **Scan gate.** `python engine\tools\validate.py scan <file>`. It prints `VALID scan 1.0.0`, or `INVALID $.path: rule`.
4. **Engine.** `python -m antigravity_engine --in … --out out\contract-check --baseline … --json-only`, run with the `engine` folder as working directory (§4.7). It writes `report.json` and `evidence.json` into `out\contract-check\` only. Any non-zero exit fails, including 2 (invalid input) and 3 (render failure).
5. **Report gate.** `validate.py report`, then `CONTRACT OK`.

No network calls, no registry or system changes, no execution-policy change.

## 3. Tests written

| Test | What it checks | Why it matters |
|---|---|---|
| Bad RunId exits 64 with fixed text and writes nothing | `-RunId bad` → 64, stderr exactly `Bad -RunId`, no file | §3.3 exit code; no half-written run |
| Upper-case hex RunId exits 64 | `…Z_ABCD` rejected | Old check let it through; the schema would then reject the scan |
| RunId with trailing newline exits 64 | `…Z_abcd` + newline rejected | `run_id` names a folder and goes into evidence (Socrates Q1) |
| Bad -Only value exits 64 with fixed text | `-Only Nope` → 64 | §3.3 exit code |
| OutputPath with RunId writes that run_id | file's `run_id` equals the given id | Run folder matches `scan.json` (§5.6 step 8) |
| Only Backup with OutputPath prints exactly AG-PHASE:backup | markers only for probes that run, nothing else on stdout | §4.8 progress; app parses stdout line by line |
| contract-check passes on this PC | real collector → `CONTRACT OK`, exit 0 | §6.3 step 2.8 |
| contract-check passes every scan fixture | all 5 `scan.*.json` (count asserted) → OK | Fixtures still match the merged engine |
| contract-check fails loudly on a broken scan | bad `run_id` → `INVALID $.run_id…`, `CONTRACT BROKEN at scan`, exit 1 | The gate must fail loudly (§6.3) |
| contract-check fails when the engine exits 2 | stub Python whose engine exits 2 → `CONTRACT BROKEN at engine` | Engine failures stop the build |
| contract-check fails when engine Python is missing | → `CONTRACT BROKEN at setup` | No silent pass on a machine without the venv |

## 4. Test results

Tests first (before any implementation):
```
FAIL Bad RunId exits 64 with fixed text and writes nothing: exit code was 1
FAIL Upper-case hex RunId exits 64 (schema wants lower case): exit code was 0
FAIL Bad -Only value exits 64 with fixed text: exit code was 1
PASS OutputPath with RunId writes that run_id
PASS Only Backup with OutputPath prints exactly AG-PHASE:backup
FAIL contract-check passes on this PC and prints CONTRACT OK: contract-check.ps1 is empty or missing
...
2 passed, 7 failed
```
The two early passes cover behaviour that already existed from Phase 1. After Socrates' review, the newline test also failed first: `FAIL RunId with trailing newline exits 64: exit code was 0`.

Two problems were caught along the way and fixed:
- **The read-only guard (§3.7)** flagged `collector.ps1:14 method not allowed: ContainsKey`. The code now uses `$PSBoundParameters.Keys -contains`, with no allowlist change.
- **`contract-check` swallowed the validator's `INVALID` line.** The function's echo was being captured by the assignment of its result. The function now returns its results through script variables instead.

Final gate (all phases):
```
Test-Common exit 0 :: 22 passed, 0 failed
Test-Skeleton exit 0 :: 14 passed, 0 failed
Test-ReadOnlyGuard exit 0 :: Passed: 292  Failed: 0
Test-ReadOnly exit 0 :: READ-ONLY OK
Test-ProbesA exit 0 :: 43 passed, 0 failed
Test-ProbesB exit 0 :: 51 passed, 0 failed
Test-Collector exit 0 :: 7 passed, 0 failed
Test-Integration exit 0 :: 11 passed, 0 failed
1/4 Collector -DryRun
2/4 validate.py scan
VALID scan 1.0.0
3/4 engine --json-only
4/4 validate.py report
VALID report 1.0.0
CONTRACT OK
contract-check exit 0
```

## 5. Run it yourself

All from `C:\Users\HP\antigravity`:

1. `powershell -NoProfile -ExecutionPolicy Bypass -File installer\contract-check.ps1`
   You should see four step lines, `VALID scan 1.0.0`, `VALID report 1.0.0`, then `CONTRACT OK`.
   - `CONTRACT BROKEN at scan` with an `INVALID $.…` line: the collector's output disagrees with the schema. Fix it on the collector side, or raise a §0.10 PR if the schema is wrong.
   - `at setup`: the engine venv or the baseline file is missing.
2. `powershell -NoProfile -File collector\tests\Test-Integration.ps1` → `11 passed, 0 failed`.
3. `mkdir out\int -Force; powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -OutputPath out\int\scan.json -RunId 2026-11-14T21-30-00Z_0001` (§6.3 step 2.2). You should see six `AG-PHASE:` lines (host, backup, patch, software, protection, recovery), exit 0, and `out\int\scan.json` with that `run_id`.
4. `powershell -NoProfile -File collector\collector.ps1 -DryRun -RunId BAD; $LASTEXITCODE` → `Bad -RunId`, then `64`.
5. §6.3 step 2.4 (repeat elevated, and on Dev-2) is yours to do by hand.

## 6. Decisions and limits

- **Manual inconsistency (open question 2, not answered):** the integration table near line 5046 gives the `-RunId` pattern as `^[0-9TZ:-]+_[0-9a-f]{4}$`. §3.3 and the schema use the strict pattern, and the code follows §3.3 (now also case-sensitive, ASCII-only and newline-safe). Suggest correcting the table.
- **The schema's `run_id` pattern also ends in `$`**, so Python's validator accepts a trailing newline too (Socrates Q1). The collector now rejects it. Tightening the schema is a §0.10 contract change, so it's left for the team.
- **Not every bad argument exits 64** (Socrates Q2). PowerShell still exits **1** before our code runs for: an unknown parameter, `-RunId` or `-Only` with no value, and `-DryRun:maybe`. Under `-File`, `-Only Backup,Host` arrives as one string and exits 64, so more than one `-Only` value only works via `-Command`. Electron treats any non-zero exit as failure, so nothing breaks.
- **Under `-DryRun`, the gate checks text that went through the console code page** (Socrates Q3). Characters outside that code page become `?`. This can't change pass/fail: a code-page round trip can't produce `"` or `\`, and `ConvertTo-Json` escapes control characters. But it is not byte-identical to the `-OutputPath` write the app uses. §6.3 specifies `-DryRun`, so this is kept as specified; the real scan on this PC has no non-ASCII characters.
- **Untested failure branches** (Socrates Q4): a collector non-zero exit and an invalid `report.json` have no test (checked by reading the code). The engine branch is now tested.
- **Unexpected errors** in `contract-check.ps1` (e.g. `out\` locked) exit 1 with PowerShell's own error text, which includes paths, and no `CONTRACT BROKEN` line. Python tracebacks are echoed word for word. This is build-time output, not product output, so POPIA (South Africa's data-protection law) is unaffected (Socrates Q5).
- **`build-all.ps1` step 0** (calling `contract-check.ps1`, §5.8) is Schwan's file and still empty. Not touched.
- **`origin/feat/engine-run-id`** (Tshedi: engine `--run-id`, `--org`) touches only the engine and doesn't affect this phase.
- **`main`'s manual** reverted five of the §0 corrections from the contract PR: `hotfix_count` type, the `duration_ms` comment, the Fixture 2 text and the `types.ts` line. This branch keeps the corrected text; Tshedi should fix `main`.
- `contract-check.ps1` is called without `-ExecutionPolicy Bypass` for the inner collector run. A child `powershell.exe` inherits the policy the parent was started with (§6.3 starts it with Bypass).

## 7. Pitch line

Every installer build first proves, end to end on a real PC, that the collector's output and the engine's report still match the shared contract, and it refuses to build if they don't.
