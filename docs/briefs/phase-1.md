# Phase 1 brief: Collector skeleton

Branch `brick/collector`. Manual §3.2–§3.4, §3.8, §3.10. Not committed yet (waiting for `Verified`).

## 1. What was built

| File | What it does and why |
|---|---|
| `collector/collector.ps1` | Entry script from §3.2. Reads the five parameters (§3.3), loads `lib/Common.ps1`, every file in `probes/`, then the optional mock, runs each probe and writes `scan.json` (or prints it with `-DryRun`). Exit codes: 0 success, 64 bad arguments, 70 cannot write, 1 any other failure. |
| `collector/lib/Common.ps1` | Shared helpers: `Invoke-Probe` (turns errors into `ok`/`unavailable`/`failed`, §0.9), `ConvertTo-AgSafeError` (removes paths and names from error text), `Test-AgAdmin`, `ConvertTo-IsoUtc`, `Get-AgHash`, `Write-ScanJson`. It also holds 22 `Read-Ag*` readers, thin one-line reads that mocks can replace (§3.10). |
| `collector/lib/Allowlist.ps1` | `$AgAllowedCommands`: exactly the 24 command names allowed by §3.7. Phase 2's guard will use it. |
| `collector/probes/.gitkeep` | Keeps the empty `probes/` folder in git; without it `collector.ps1` stops at the load step. |
| `collector/tests/Test-Common.ps1` | 22 unit tests for `Common.ps1` and `Allowlist.ps1`. |
| `collector/tests/Test-Skeleton.ps1` | 14 end-to-end tests. Each one starts `collector.ps1` in a fresh `powershell.exe` and checks exit code, stdout, stderr and the written file. |
| `collector/tests/stubs/stub-probes.ps1` | Fake `Get-Ag*` probes with fixed values, loaded through `-MockFile`. The real probes arrive in Phases 3–4. |
| `collector/tests/stubs/mock-edition.ps1` | Replaces one reader (`Read-AgEdition`). It proves a mock file overrides the real reader all the way to the output. |

## 2. How it works

1. `collector.ps1` checks parameters. A bad `-Only` or `-RunId` is rejected by PowerShell itself (exit 1). A missing `-MockFile`, or neither `-OutputPath` nor `-DryRun`, gives a fixed message and exit 64.
2. It loads `Common.ps1`, then `probes\*.ps1`, then the mock. The mock is loaded last, so its functions win.
3. It builds the header (`schema_version`, `run_id`, `collector_version`). `run_id` is the UTC time plus 4 random hex digits, formatted with the invariant culture (a fixed, language-neutral format) so a Thai-calendar PC can't write year 2569.
4. For each of the 6 sections it prints `AG-PHASE:<name>` (only when writing a file, so `-DryRun` stdout stays pure JSON) and runs the probe.
5. `Write-ScanJson` converts to JSON with `-Depth 8`. It writes with `[IO.File]::WriteAllText`, UTF-8 without a byte-order mark (BOM, 3 hidden bytes some tools add at the start). It writes only the exact `-OutputPath` and never creates folders. On failure: fixed text, exit 70.
6. A top-level `trap` catches anything unexpected. It prints `Collector failed` and exits 1, so no file path ever reaches stderr.

**What each operation touches (all read-only):**

| Operation | Touches | Why safe |
|---|---|---|
| `Get-CimInstance` (`Win32_OperatingSystem`, `Win32_ShadowCopy`, `SecurityCenter2\AntiVirusProduct`) | WMI (Windows' built-in system-information service) query | Query only; `Win32_Product` is never used (§3.5) |
| `Get-ItemProperty` / `Test-Path` on HKLM/HKCU keys from §3.5 | Registry values | Reads only; no `Set-`/`New-` anywhere |
| `Get-Service`, `Get-HotFix`, `Get-MpComputerStatus`, `Get-MpPreference`, `Get-BitLockerVolume`, `Get-ComputerRestorePoint`, `Get-WinEvent -MaxEvents 1` | Status reads | `Get-` verbs only |
| `New-Object -ComObject Shell.Application` → `ExtendedProperty('System.Volume.BitLockerProtection')` | One volume property | Reads a property; the allow-listed COM (Windows component interface) fallback from §3.5 |
| `& "$env:SystemRoot\System32\reagentc.exe" /info` | Recovery-environment status | Full path (no search-path trickery), literal `/info` only (§3.7) |
| `[IO.File]::WriteAllText(-OutputPath)` | One file | The only write the collector makes (§3.7 rule 5) |
| SHA-256 of salt + computer name | Memory only | Hostname is never stored raw (§0.5 POPIA) |

**No reader is called in Phase 1**: no probes exist yet, and the tests never call the readers (they would touch the real system). Phase 1 only checks that the readers exist and can be replaced.

## 3. Tests written

**Test-Common.ps1 (22)**

| Test | Checks | Why it matters |
|---|---|---|
| IsoUtc null returns null / known date / fixed UTC input | `$null`→`$null`; `2026-11-14T16:42:07Z` exactly | Engine rejects `\/Date()\/` (§3.8) |
| IsoUtc ignores thread culture | Same string under `th-TH` | Thai Buddhist calendar would shift the year |
| IsoUtc rejects non-DateTime | A raw number throws | Stops a raw FILETIME (Windows' number-of-ticks date format) silently becoming year ~400 |
| Invoke-Probe ok / unavailable / failed | Statuses, key order, template keys present as `null`, `"Type: message"`, ≤200 chars | §0.9 / §3.4 contract |
| Invoke-Probe failed scrubs sensitive text | Paths, UNC, SID, username, computer name removed | POPIA (§3.4 rule 4) |
| SafeError keeps plain text | Fixed messages unchanged | No mangling of normal errors |
| SafeError scrubs path with spaces / path variants / any SID | `C:\Users\John Smith\…`, `C:/…`, `file:///…`, `\\?\…`, `\\srv\share\a b`, `S-1-12-1-…` | Gaps Socrates found (Q1) |
| SafeError redacts whole-word user name only | `HP` redacted; `xHPy` left alone | Readable errors (Q11) |
| Get-AgHash format and behaviour | `^sha256:[0-9a-f]{64}$`, deterministic, input not visible | Hostname privacy (§0.5) |
| Write-ScanJson file output | No BOM; parses; 1-item arrays stay arrays; deep nesting kept | All four §3.8 traps |
| Write-ScanJson DryRun | No file; returns JSON | `-DryRun` writes nothing (§3.3) |
| Test-AgAdmin returns bool | Type check | Scoring depends on it |
| All Read-Ag readers exist / Mock override wins | 22 readers defined; redefinition wins | Mocks are how we test without changing the PC (§3.10) |
| Allowlist has exactly the 24 names | No extras, none missing | Allow-list is frozen to §3.7 |
| Every collector .ps1 has UTF-8 BOM | First bytes `EF BB BF` (empty files skipped) | PS 5.1 misreads non-ASCII without BOM (§7) |

**Test-Skeleton.ps1 (14)**

| Test | Checks | Why it matters |
|---|---|---|
| No OutputPath and no DryRun exits 64 | Exit 64; stderr exactly the fixed text, no path/username | §3.3 + POPIA |
| Bad RunId fails and writes nothing / Bad -Only value fails | Non-zero exit, no file | Bad input never produces output |
| DryRun emits valid contract header | Pure JSON, no `AG-PHASE`, key order, versions, `run_id`/`collected_at` formats, integer `duration_ms` | §0.5 header |
| DryRun honours supplied RunId | `run_id` = given value | Run folder must match (§3.3) |
| OutputPath writes file and phase markers | File, no BOM; stdout exactly 6 `AG-PHASE:` lines in order | App progress bar (§4.8) |
| DryRun with OutputPath creates no file | `-DryRun` wins | §3.3 |
| Only Host,Patch / Only Protection via -File | Only the asked sections | Isolated testing (§3.9) |
| Unwritable OutputPath exits 70 and creates no folder | Exit 70, fixed stderr, folder not created | §3.7 rule 5 |
| Missing MockFile exits 64 with fixed text | Exit 64, `Mock file not found` | Bad argument, no path leak |
| Uncaught probe error exits 1 with fixed text | Exit 1, `Collector failed`, no path | Nothing private in stderr |
| Mock override of Read-AgEdition reaches output | `host.os_edition == 'MockCore'` | Proves §3.10 load order end-to-end |
| Run under th-TH culture keeps Gregorian year | `run_id`/`collected_at` start with `20` | Real bug found and fixed |

## 4. Test results

**Tests first (before any implementation)**, all failing for the right reason:
```
FAIL IsoUtc null returns null: The term 'ConvertTo-IsoUtc' is not recognized as the name of a cmdlet, function, script file, or operable program.
FAIL Invoke-Probe unavailable: The term 'Invoke-Probe' is not recognized ...
FAIL Allowlist has exactly the 24 names: $AgAllowedCommands not defined
0 passed, 15 failed            (Test-Common, exit 1)
FAIL No OutputPath and no DryRun exits 64: collector.ps1 does not exist
0 passed, 9 failed             (Test-Skeleton, exit 1)
```
**Review-fix tests first** (written before the Socrates fixes):
```
FAIL SafeError scrubs path with spaces in user name: leaked: Access to <path> Smith\AppData\x denied
FAIL Run under th-TH culture keeps Gregorian year: run_id was 2569-10-27T23-48-21Z_106e
FAIL No OutputPath and no DryRun exits 64: stderr was 'C:\Users\HP\antigravity\collector\collector.ps1 : Use -OutputPath <file> or -DryRun
17 passed, 5 failed  (Test-Common)    9 passed, 5 failed  (Test-Skeleton)
```
**Final gate** (Phase 1 is the first collector phase; `Test-ReadOnly.ps1` starts in Phase 2):
```
22 passed, 0 failed
exit=0
14 passed, 0 failed
exit=0
```
Test changes during the phase, both test defects, not code fixes: (1) test m skips 0-byte files, because `collector/docs/demo/reset-demo.ps1` is an empty placeholder. (2) The child-process helper ran with `$ErrorActionPreference='Stop'`, which turned the child's stderr into a crash before the exit code could be read; it now uses `Continue`. The multi-value `-Only` test now runs through `-Command` (see §6).

## 5. Run it yourself

Working folder: `C:\Users\HP\antigravity`

```powershell
powershell.exe -NoProfile -File collector\tests\Test-Common.ps1
powershell.exe -NoProfile -File collector\tests\Test-Skeleton.ps1
```
Expect `22 passed, 0 failed` and `14 passed, 0 failed`. Any `FAIL <name>: …` line names the broken behaviour. `is not recognized` means a file is missing from `collector\lib`.

Working folder: `C:\Users\HP\antigravity\collector`

```powershell
powershell.exe -NoProfile -File .\collector.ps1 -DryRun -MockFile .\tests\stubs\stub-probes.ps1
```
Expect one JSON document with the 6 sections and stub values. Without `-MockFile` you'll see `Collector failed` and exit 1. That's expected until Phase 3: there are no real probes yet.

You don't need `-ExecutionPolicy Bypass`: your CurrentUser policy is `RemoteSigned`, which runs local scripts.

## 6. Decisions and limits

**Decisions taken (Archon):** A, error text is scrubbed rather than fixed-only. B, bad `-Only`/`-RunId` exit 1 (manual skeleton kept). C, salt `antigravity-host-v1` (changing it changes every hostname hash).

**Manual vs code, needs your OK to update the manual (§1 rule: manual first):**
1. §3.8 `ConvertTo-IsoUtc` uses `$d.Value`. In PS 5.1 a `[Nullable[DateTime]]` parameter arrives as a plain `DateTime`, so `.Value` is `$null` (verified). The code uses an untyped parameter, rejects non-dates, and uses the invariant culture.
2. §3.2/§3.8 use `Write-Error … ; exit 64/70`. Under `$ErrorActionPreference='Stop'` that crashes with exit 1 before `exit` runs. It also prints `At C:\Users\<name>\…\collector.ps1:20` (a username in the path). The code uses `[Console]::Error.WriteLine('<fixed text>')`, and adds a top-level `trap` (exit 1, `Collector failed`) and a `-MockFile` existence check (exit 64).
3. §3.3 exit-code table should list 1 = invalid `-Only`/`-RunId` or unexpected failure.
4. §3.2 `run_id` needs the invariant culture (Thai-calendar bug).

**Limits:**
- `-Only` with several names works only from a PowerShell prompt or `-Command` (`.\collector.ps1 -Only Host,Patch`), not through `powershell -File`, which passes `Host,Patch` as one string. One name works everywhere (the §3.9 form).
- When PowerShell rejects `-Only`/`-RunId` itself, its message includes the script path. If the app is installed under a user's profile, that path contains the username. The text goes to stderr only, never into `scan.json`. Open question: does Electron log stderr? If so, Frank/Schwan should not log it verbatim.
- The scrubber removes everything from a path's start to the next quote or the end of the message. It errs on the side of removing too much. A username that differs from the profile folder name and appears outside a path isn't caught. Fixed messages remain the first defence.
- `Read-AgReagentc` keeps going when reagentc writes to stderr (local `Continue`). It is not tested here, because tests never run real readers.
- Constrained Language Mode (a locked-down PowerShell mode) isn't supported: PS classes don't work there (§3.6, STRETCH).

**Socrates' questions, answered:**
| # | Answer |
|---|---|
| 1, 2 | Fixed: scrubber rewritten, 4 new tests |
| 3 | Fixed: local `Continue` in `Read-AgReagentc`, output returned as strings |
| 4, 7 | Fixed: fixed-text stderr, `trap`, mock check; stderr now asserted. Binding-error path left as a recorded limit |
| 5 | Deferred to Phase 2 (`Test-ReadOnly` design): §3.7's guard as written flags our own helpers (`Read-Ag*`, `Write-ScanJson`, …) and can't read the name in `& "$env:SystemRoot\…\reagentc.exe"`. Plan: exempt functions defined in `collector/lib`, and flag or special-case dynamic `&` calls. The allow-list itself stays unchanged |
| 6 | Fixed: `mock-edition.ps1` end-to-end test |
| 8 | Fixed: literal expected value + `th-TH` tests |
| 9 | Rule for Phases 3–4: PowerShell unwraps a one-item array when a function returns it, so probes must wrap reader output again, e.g. `@(Read-AgHotFix)` |
| 10 | Fixed: non-DateTime input throws |
| 11 | Fixed: whole-word redaction |

**Housekeeping:**
- `.offline/` is still tracked in git despite `.gitignore` (raised before Phase 1; your call).
- A stray `python.exe` (PID 23256) left over from a helper's shell may still be running. I didn't stop it (rule §6); you can close it in Task Manager.

## 7. Pitch line

The collector's skeleton proves, with 36 automated tests, that it writes exactly one file, says nothing personal even when it crashes, and gives the same answer on any language of Windows.
