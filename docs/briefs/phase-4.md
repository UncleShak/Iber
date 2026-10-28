# Phase 4 brief: Backup, Patch, Software, Recovery probes (+ Phase 5: mocks complete)

Branch `brick/collector`. Manual §3.5 (items 1, 2, 3, 5), §3.6, §3.10, §0.9. Pre-verified by the Archon; committed and pushed. **Phase 5 is done too**: every mock case in §3.10 now runs, with none pending.

## 1. What was built

| File | What it does and why |
|---|---|
| `collector/probes/Backup.ps1` | `Get-AgBackup`: File History (on/off and last backup), the last Windows Backup success (event 4), OneDrive folder protection (folder names only, never paths), shadow-copy count, backup agents from other vendors (vendor names, P4). |
| `collector/probes/Patch.ps1` | `Get-AgPatch`: hotfix count, newest install date, the 10 newest as `{kb, installed_on}`, days since the last update, pending reboot. IDs that aren't KB numbers are counted but not listed (P2). If no hotfix has a date → `unavailable`. |
| `collector/probes/Software.ps1` | `Get-AgSoftware`: the 3 uninstall locations in the registry, filtered per §3.5, trimmed and cut to the schema's lengths (P1). Duplicates removed, at most 500 entries. |
| `collector/probes/Recovery.ps1` | `Get-AgRecovery`: WinRE (the Windows recovery environment) from `reagentc /info` (admin only), System Restore from the registry, restore-point count and latest point (admin only). |
| `collector/mocks/healthy.ps1` | Adds healthy values for every new reader, so no mock run ever reads this PC. |
| `collector/tests/Test-ProbesB.ps1` | 50 unit tests. Every reader is faked. |
| `collector/tests/Test-Collector.ps1` | Now a full run (all 6 sections) for each mock. `stale-patches` and `probe-throws` are switched on. **Every** mock output is checked against the whole `scan.schema.json`. |
| `collector/tests/Test-ReadOnly.ps1` | `$AgPendingProbes` is removed, since all 6 probes exist. 3 reviewed allowlist entries added (Tshedi to review): the type `Management.ManagementDateTimeConverter`, and the static methods `DateTime.FromFileTimeUtc` and `ManagementDateTimeConverter.ToDateTime`. All three are pure date conversions. |
| `collector/docs/decisions.md` | P1–P6 and the known limits. |

## 2. How it works

- **Admin-only fields** (P3): shadow copies, the backup event, WinRE and restore points are decided by `Test-AgAdmin`. When not admin, the reader **isn't called**, so reagentc never runs; the field is `null` and the section stays `ok`.
- **Bad single values** (P6): if one raw value can't be read or converted, only that field becomes `null`. That covers an invalid File History time, `Get-ComputerRestorePoint` throwing, and reagentc missing. The rest of the section's evidence is kept.
- **No backup events / no backup log:** recognised by PowerShell's error ID (`NoMatchingEventsFound`, `NoMatchingLogsFound`), which is the same in every language, so non-English Windows works. Any other error → `failed`.
- **Dates:** ISO UTC through `ConvertTo-IsoUtc`, and `installed_on` as `yyyy-MM-dd` in the invariant culture (a fixed, language-neutral format), so a Thai-calendar PC can't shift the year.

**What it touches:** only the `Read-Ag*` readers from Phase 1 (`Get-HotFix`, `Get-ItemProperty` on the §3.5 keys, `Get-WinEvent -MaxEvents 1`, `Get-CimInstance Win32_ShadowCopy`, `Get-ComputerRestorePoint`, `Get-Service`, `reagentc.exe /info`). All are reads. Nothing is written.

## 3. Tests written

| Suite | Cases | Covers |
|---|---|---|
| Test-ProbesB | 50 | Each §3.5 rule; P1–P4; non-admin readers not called; non-English "no events" error IDs; an unrelated error → failed; invalid FILETIME and byte[] → null; restore points throwing → null with the rest kept; reagentc missing; a KB ID with a trailing newline left out; th-TH formatting; single-item arrays surviving JSON; the software reader throwing → failed with cleaned-up text. |
| Test-Collector | 7 | healthy, home-edition, defender-off, stale-patches (days since ≥ 75), non-admin (all admin-only fields null, every status `ok`), probe-throws (software `failed`, others `ok`), no mock. Each output is validated against the full schema. |

## 4. Test results

```
Test-Common         22 passed, 0 failed
Test-Skeleton       14 passed, 0 failed
Test-ProbesA        43 passed, 0 failed
Test-ProbesB        50 passed, 0 failed
Test-Collector      7 passed, 0 failed
Test-ReadOnlyGuard  Passed: 292  Failed: 0
Test-ReadOnly       READ-ONLY OK
```

The whole gate takes about 35 seconds.

Proof the tests came first:
- Probes: `1 passed, 43 failed` (the probes didn't exist yet).
- Socrates fixes: `43 passed, 8 failed`, e.g. `FAIL Backup: error id 'NoMatchingEventsFound' with a non-English message gives null, ok: got failed InvalidOperationException: Es wurden keine Ereignisse gefunden…`.

**Review (Socrates, one round):**
- One BUG: non-English "no events" → backup marked `failed`. Fixed.
- Two RISKs were fixed as P6: an invalid FILETIME or a throwing restore-point read wiped out the whole section.
- The KB-pattern nit was fixed.
- Mock outputs are now all schema-checked.
- The fixes weren't re-reviewed (one-round rule).

## 5. Run it yourself

Working folder `C:\Users\HP\antigravity`:

```
powershell.exe -NoProfile -File .\collector\tests\Test-ProbesB.ps1
powershell.exe -NoProfile -File .\collector\tests\Test-Collector.ps1
powershell.exe -NoProfile -File .\collector\tests\Test-ReadOnly.ps1
```

You should see the lines in §4. A `FAIL` line names the rule that broke.

**Full scan on this PC** (read-only, nothing saved), from `C:\Users\HP\antigravity\collector`:

```
powershell.exe -NoProfile -File .\collector.ps1 -DryRun
```

You should see one JSON document with 6 sections. Run it once as admin and once without: without admin, the shadow-copy, backup-event, WinRE and restore-point fields should be `null`. Please record the ⚠ verify values (P5) in `collector/docs/decisions.md`: the BitLocker COM value, File History `ProtectedUpToTime` (only on a PC with File History set up), and System Restore `RPSessionInterval`/`DisableSR`. Don't save or commit the output.

## 6. Decisions and limits

- P1–P6 as recorded in `collector/docs/decisions.md`. **P6 is new** (from the review): one unreadable value becomes `null` for that field only. §3.5 doesn't cover it, so the manual should add a line.
- **3 allowlist additions need Tshedi's review** (§1).
- **Limits:**
  - `days_since_latest_hotfix` can be -1 for a patch installed between 00:00 and 02:00 South Africa time. That follows the manual's formula, and the engine recomputes it anyway.
  - The th-TH test proves formatting only, not how `Get-HotFix` parses dates.
  - Software names can in theory contain a user name; that is out of scope, per §3.5.
- **Open questions carried over:**
  - `-MockFile` restriction (Phase 2, L3).
  - `AMRunningMode` / passive Defender (Phase 3, L1).
  - Manual §3.7 snippet update (Phase 2, D1).
- **Next: Phase 6 (licence).**

## 7. Pitch line

"The scan collects only the evidence a backup or patch check needs (folder names, never paths; dates, never files), and one unreadable value never wipes out the rest of the evidence."
