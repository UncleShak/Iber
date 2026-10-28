# Integration Phase 6.4 - clean-VM test (manual 5.9, Brick D checklist D6)

Build under test: whichever installer the builder hands over (e.g. RC1,
`Antigravity-Setup-1.0.0.exe`). Fill in before starting, from the builder's report:

- Commit built from: ______  Version: ______
- Size: ______ bytes (expect ~100-150 MB, must be < 200 MB)
- SHA-256 (from the builder's `SHA256SUMS.txt`): ______
- Earlier reference build: `Antigravity-Setup-0.1.0.exe` from `v0.1.1-integrated` (bf7b1f1),
  101,282,538 bytes, SHA-256 B87FF471... (Dev-1, 28 Oct 2026). Do not expect this hash for RC1.
- Files to copy into the VM: `desktop\release\Antigravity-Setup-<version>.exe` and
  `desktop\release\SHA256SUMS.txt`; for the smoke test also the repo `installer\` folder.

VM: Schwan's Hyper-V VM, Windows 11, no Python/Node/Git, Defender on with real-time
protection, a standard user and an admin account. Revert to `clean-baseline` before starting.

Have to hand: demo key AG-DEMO-0001 token (`shared/license/demo-keys.md`); the expired test
token (`tools/demo-tokens.txt`, git-ignored: never on screen or in a commit).

Fill in Result (PASS / FAIL) and Notes for each step. Steps 1-14 are the minimum for 6.4.

| # | Step | Expected result | Result | Notes |
|---|---|---|---|---|
| 1 | Hyper-V Manager: apply checkpoint `clean-baseline`; start the VM | VM boots to the desktop | | |
| 2 | VM Settings -> Network Adapter -> Not connected | No network (proves offline operation) | | |
| 3 | Copy the Setup exe and `SHA256SUMS.txt` into the VM (Enhanced Session clipboard or shared VHD) | Files on the VM desktop | | |
| 4 | In the VM (cwd: Desktop): `Get-FileHash .\Antigravity-Setup-*.exe -Algorithm SHA256` | Same hash as `SHA256SUMS.txt` and the builder's report | | |
| 5 | Log in as the standard user; double-click the installer | Wizard appears; no UAC prompt. SmartScreen may appear -> More info -> Run anyway (manual 5.7) | | |
| 6 | Accept defaults; finish with "Run Antigravity" ticked. Then `smoke-test.ps1 -Phase AfterInstall` (below) | App opens on the License screen within 5 s; desktop and Start menu shortcuts exist; smoke test passes | | |
| 7 | Enter the invalid key `AG1.xxx.yyy` | "That doesn't look like an Antigravity key..." | | |
| 8 | Enter the expired test token | "This key expired on ..." | | |
| 9 | Enter the AG-DEMO-0001 token | Main screen with "Start scan"; footer shows licence id | | |
| 10 | Click "Start scan"; time it | Progress moves through all phase messages; Results in < 60 s; admin hint shown | | time: |
| 11 | Check the Results | 5 categories; admin-only items "Not checked"; top fixes listed; page styled (cards, spacing); footer shows `Evidence ID: AG-` + 12 characters | | |
| 12 | Click "Open one-page action plan (PDF)" | PDF opens in Edge; exactly one page; same Evidence ID as the footer | | |
| 13 | Click "Open full report" | HTML opens in Edge, offline, colours correct | | |
| 14 | Windows Security -> Protection history | No detections of Antigravity, PowerShell or engine.exe | | |
| 15 | Close the app; right-click the shortcut -> Run as administrator (admin credentials); scan again | More rows rated (shadow copies, restore points, Windows Backup, recovery tools); still < 60 s | | time: |
| 16 | Close and reopen the app | Goes straight past the License screen (licence remembered) | | |
| 17 | Open `%LOCALAPPDATA%\Antigravity\runs` | Exactly one run folder (older run deleted) | | |
| 18 | Open that run's `scan.json`; search for the VM's username and computer name | Neither appears (POPIA) | | |
| 19 | Settings -> Apps -> Installed apps -> Antigravity -> Uninstall. Then `smoke-test.ps1 -Phase AfterUninstall` | Uninstaller completes without UAC; smoke test passes | | |
| 20 | Check `%LOCALAPPDATA%\Programs\Antigravity`, `%APPDATA%\Antigravity`, `%LOCALAPPDATA%\Antigravity` and the shortcuts | All gone | | |
| 21 | Apply checkpoint `clean-baseline` again | VM ready for the next build | | |

## Smoke test (steps 6 and 19)

Copy the repo `installer` folder to the VM desktop, then:

```powershell
# cwd: (in VM) Desktop\installer
powershell -NoProfile -ExecutionPolicy Bypass -File .\smoke-test.ps1 -Phase AfterInstall
powershell -NoProfile -ExecutionPolicy Bypass -File .\smoke-test.ps1 -Phase AfterUninstall
```

## Known items for this build (not failures of 6.4)

- Manual 5.9 step 15 lists BitLocker among the extra rows; on Windows Home it stays
  "not available on Windows Home" (rating amber), which is correct.
- Recovery may show "System Restore: Off" while restore points exist (open question on the
  manual 3.5 registry method, Brick B). Note what Settings -> System Protection shows for C:.

## Record

One line in `docs/decisions.md`: date/time, build (version, commit, first 8 hex of SHA-256),
pass/fail, and the step number of any failure.
