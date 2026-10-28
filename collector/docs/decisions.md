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

## 2026-10-28 · Phase 4 (agreed in plan) · Probes B

- P1 Software: cut name/publisher to 256 and version to 64 characters (schema limits); drop entries whose name is blank after trimming.
- P2 Patch: hotfix IDs not matching `^KB\d+$` are left out of `hotfixes` but still counted in `hotfix_count`.
- P3 Admin-only fields (shadow copies, restore points, backup event, WinRE) are set from `Test-AgAdmin`; non-admin → `$null` whatever the reader returns (Win32_ShadowCopy can quietly return 0).
- P4 Third-party backup agents: vendor names (`Veeam`, `Acronis`, `Macrium`, `Backblaze`, `Carbonite`, `Datto`, `Synology Active Backup`, `CrashPlan`, `IDrive`), no duplicates, in the §3.5 list order.
- P5 ⚠ verify values (BitLocker COM, File History `ProtectedUpToTime`, System Restore `RPSessionInterval`/`DisableSR`) are checked by hand on a real PC and recorded here.
- P6 (from the Socrates review): a single field whose raw value can't be read or converted falls back to `$null` for that field only, and the section stays `ok`. This covers a File History FILETIME that is invalid or not an integer, Get-ComputerRestorePoint throwing while elevated, and reagentc.exe missing. Reason: one bad value must not wipe out the rest of the section's evidence (backup is rated red on missing evidence). §3.5 doesn't cover this case.
- The "no backup events / no log" check uses `FullyQualifiedErrorId` (`NoMatchingEventsFound`, `NoMatchingLogsFound`), not the message text, which is translated on non-English Windows.
- Known limits: `days_since_latest_hotfix` can be -1 for a patch installed between 00:00 and 02:00 SAST (the manual's formula; the engine recomputes it). The th-TH test only covers formatting, not how Get-HotFix parses dates.

## 2026-10-28 · Prep-night verify values (Archon's PC: Windows 11 Home Single Language, build 26200)

- BitLocker COM `System.Volume.BitLockerProtection` = `1` while `Get-BitLockerVolume` ProtectionStatus = `On` → the mapping 1 = on is confirmed. Values 2 and 3 are not yet seen.
- File History: not configured on this PC, so the `ProtectedUpToTime` type is **still unverified**.
- System Restore `RPSessionInterval`/`DisableSR`: **still unverified**.
- Software: real uninstall entries can end in a NUL character (e.g. "Roblox Player for HP\0"). Control characters are now stripped in `Software.ps1`.
- **Open question (manual §3.5/§3.6):** this Home PC has device encryption **on** and `Get-BitLockerVolume` works, but the Home precondition reports `bitlocker: unavailable`. The real evidence ("on") is lost, and the engine rates it amber. Should Home still try the cmdlet/COM read and report the value when one is readable?
