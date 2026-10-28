# Phase 3 brief: Host and Protection probes (+ Phase 5 part 1: mocks)

Branch `brick/collector`. Manual §3.5, §3.6, §0.9, §3.10. Pre-verified by the Archon; committed and pushed.

## 1. What was built

| File | What it does and why |
|---|---|
| `collector/probes/Host.ps1` | `Get-AgHost`: the 6 host fields (§3.5). Not wrapped in `Invoke-Probe`, because the schema's `host` block has no status. If a host read fails, the collector stops with "Collector failed" (D1). A build number that isn't all digits throws `OS build unreadable`. |
| `collector/probes/Protection.ps1` | `Get-AgProtection` returns `bitlocker`, `defender`, `cfa` and `asr`. Each is its own `Invoke-Probe`, so one failing doesn't stop the others. Sub-probes: `Get-AgDefender`, `Get-AgCfa`, `Get-AgAsr`, `Get-AgBitLocker`. |
| `collector/lib/Common.ps1` | 3 new readers (one-line reads that mocks can replace): `Read-AgPsVersion`, `Read-AgComputerName`, `Read-AgHasBitLockerCmdlet`. |
| `collector/mocks/*.ps1` | Phase 5 part 1. `healthy.ps1` gives fixed healthy values for every Host/Protection reader. `home-edition`, `defender-off`, `non-admin`, `stale-patches` and `probe-throws` each load `healthy.ps1` first and then override, so mock runs never read this PC. |
| `collector/tests/Test-ProbesA.ps1` | 43 unit tests. Every reader is faked, and any fake left unset throws "REAL READER CALLED". |
| `collector/tests/Test-Collector.ps1` | The §3.10 isolation test: runs `collector.ps1 -DryRun -Only Host,Protection` once per mock and once with no mock. |
| `collector/tests/Test-ReadOnly.ps1` + `Test-ReadOnlyGuard.ps1` | `Get-AgHost` and `Get-AgProtection` are removed from the pending-probe list. **Speed-up:** the scan is now a function, `Invoke-AgReadOnlyScan`, and the cmdlet-name lookup is done once and cached. Most guard tests run in one process. Suite time went from **198 s to 18 s**, with the same 292 cases and identical case names. |

## 2. How it works

- **Defender:** reads `Read-AgMpStatus`. `third_party_av` is the first SecurityCenter2 (Windows' list of installed antivirus products) name that isn't blank and isn't Defender.
  - If the status read throws and the WinDefend service isn't `Running` → `ok`, with antivirus and real-time reported as off. A stopped Defender is a finding (§3.6).
  - If it throws while the service is running → `failed`.
  - A signature age above `[int]::MaxValue` (Defender's "never updated" value, 4294967295) → `null`.
- **CFA:** `Get-MpPreference`, with the two registry keys as fallback. Codes 1 and 3 → `enabled`, 2 and 4 → `audit`, 0 → `disabled`; anything else → `null`.
- **ASR:** pairs up rule IDs and actions from `Get-MpPreference`, with the registry as fallback. Actions: 0 → off, 1 → block, 2 → audit, 5 → off, 6 → warn. Unknown codes, and IDs that aren't GUIDs, are left out. Nothing configured → `rules: []`, `ok`.
- **BitLocker:**
  - On a Home edition → `unavailable`.
  - Running as admin with the cmdlet → `Get-BitLockerVolume`. The percentage is truncated (99.6 → 99).
  - Otherwise → the COM fallback: 1 → on, 2 and 3 → off.
  - If the fallback gives nothing → `unavailable` ("Requires administrator rights", or as admin "BitLocker status not readable on this PC").

**What it touches:** only the existing `Read-Ag*` readers, which are all `Get-*` cmdlets and registry reads from §3.5, plus `Get-Command Get-BitLockerVolume` to check the cmdlet exists. Nothing is written. The tests never read the real PC, except the one "no mock" case in Test-Collector, which runs `-DryRun` (nothing written) and prints only PASS/FAIL.

## 3. Tests written

| Suite | Cases | Covers |
|---|---|---|
| Test-ProbesA | 43 | Host types and order, plus a throwing read propagating. Defender: normal, passive, stopped, failed, "never" signature age, blank and non-"s" product names. CFA codes 0–4 and the fallback. ASR codes, a single rule staying an array, the fallback, non-GUID IDs. BitLocker Home, admin, non-admin COM, cmdlet missing, throws. Sub-blocks isolated from each other. Guard still OK. |
| Test-Collector | 5 + 2 pending | healthy (schema-valid via the engine venv's `jsonschema`), home-edition, defender-off, non-admin, no mock. `stale-patches` and `probe-throws` stay pending until Phase 4. |

## 4. Test results

```
Test-Common         22 passed, 0 failed
Test-Skeleton       14 passed, 0 failed
Test-ProbesA        43 passed, 0 failed
Test-Collector      5 passed, 0 failed, 2 pending
Test-ReadOnlyGuard  Passed: 292  Failed: 0
Test-ReadOnly       READ-ONLY OK
```

Proof the tests came first:
- Probes: `2 passed, 35 failed`, e.g. `FAIL Host: six fields with the right types: The term 'Get-AgHost' is not recognized`.
- Mocks: `1 passed, 4 failed, 2 pending`, e.g. `FAIL healthy: ... mock healthy.ps1 does not exist`.
- Socrates fixes: `37 passed, 5 failed`.
- My own fix: `FAIL Defender: third-party name without the letter s is kept: third_party_av was ''`.

**Review (Socrates, one round).**
- One BUG: a signature age of 4294967295 crashed the Defender block. Fixed.
- Two more treated as bugs because they produced schema-invalid output: ASR IDs that aren't GUIDs, and an empty OS build. Fixed.
- Two small fixes: the percentage rounding, and blank product names. Fixed.
- I found one more while writing this brief: the product-name filter was `'S'` instead of `'\S'`, so a name such as "Avira" was ignored. Fixed, with a test.
- These fixes weren't re-reviewed (one-round rule).

## 5. Run it yourself

Working folder `C:\Users\HP\antigravity`. Each command should end with the line shown in §4:

```
powershell.exe -NoProfile -File .\collector\tests\Test-ProbesA.ps1
powershell.exe -NoProfile -File .\collector\tests\Test-Collector.ps1
powershell.exe -NoProfile -File .\collector\tests\Test-ReadOnlyGuard.ps1
```

**Your PC check (D3)**, from `C:\Users\HP\antigravity\collector`:

```
powershell.exe -NoProfile -File .\collector.ps1 -DryRun -Only Host,Protection
```

You should see one JSON document: `host`, then `protection` with 4 blocks, each with a `status`. Check that it has no user name, path or raw computer name. Run it once normally and once as administrator: `bitlocker` should be `ok` as admin, and `ok` or `unavailable` otherwise. Please record in `collector/docs/decisions.md` the raw BitLocker COM value you see (⚠ verify, §3.5). Don't save or commit the output.

## 6. Decisions and limits

- D1/D2 are applied as agreed (see `collector/docs/decisions.md`). The text "BitLocker status not readable on this PC" is new wording; the manual doesn't give any for that case.
- **L1. `AMRunningMode` isn't read.** On a machine where Defender is in passive mode but SecurityCenter2 shows no other product, `third_party_av` stays `null`, and the engine rates Defender red. The manual needs to say what `third_party_av` should hold when only the running mode shows passive.
- **L2. Test types.** The BitLocker `ProtectionStatus`/`EncryptionMethod` fakes are strings, not the real enum types, and the COM value type isn't confirmed (⚠ verify).
- **L3.** The `-MockFile` open question from Phase 2 still stands.
- **Commits:** the guard speed-up is in the same commit as the probes. Splitting them would leave one commit where the pending-probe test fails.

## 7. Pitch line

"Every protection check reports honestly: 'off', 'not checked' or 'check failed' are never confused, so a business owner is never told they're unsafe because we couldn't look."
