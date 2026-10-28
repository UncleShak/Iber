# Collector decisions (Brick B)

## 2026-10-28 · Phase 2 · Read-only guard is a stricter version of the manual §3.7 snippet

- The §3.7 snippet fails on our own helpers (`ConvertTo-IsoUtc`, `Write-ScanJson`, `ConvertTo-AgSafeError`, `Read-Ag*`). It also misses run-time `&`/`.` calls, .NET calls and parse errors, and it skips any path containing `\tests\`.
- `collector/tests/Test-ReadOnly.ps1` replaces it. Commands, types, methods, cmdlet arguments, path arguments and run-time call sites are all allowlists or pins. The lists sit at the top of the file and, like `lib/Allowlist.ps1`, need Tshedi's review before anything is added.
- Manual follow-up: replace the §3.7 snippet with a pointer to `Test-ReadOnly.ps1`.
- Known limits: a static check can't be complete; property getters on allowed COM/CIM objects are only checked against the reflection denylist; `-MockFile` dot-sources a file the guard doesn't scan (§3.10, open question).
- `lib/Common.ps1:37` now uses `$_.CategoryInfo.Reason` instead of `GetType().Name`. The output is the same; the change lets `GetType` stay banned.
- One pin: `$p.PSObject.Properties` as the loop collection in `Read-AgAsrRegistry`. The ASR registry key holds GUID value names that aren't known ahead of time.

## 2026-10-28 · Phase 3 (agreed in plan) · Value mappings with no slot in the schema

- Host read failure: no placeholder values. The collector exits 1 with the message "Collector failed".
- BitLocker COM value `3` (encrypting) → `off`; ASR action `5` → `off`; any other unknown ASR action code → leave that rule out.
