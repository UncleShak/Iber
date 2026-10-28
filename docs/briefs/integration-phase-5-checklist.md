# Integration Phase 5 (manual 6.6) - team checklist

First full end-to-end dev-mode run on Dev-1, on a shared screen. Frank drives; Shakir, Tshedi
and Schwan each watch their part. Do the steps in order; stop at the first one that does not
show its expected result and log it in `docs/decisions.md` with its owner.

## Before you start (Frank, 2 minutes)

- On `main` at the commit being tagged; `git status` clean apart from `docs/decisions.md`.
- Engine venv present: `engine\.venv\Scripts\python.exe` exists (dev mode uses it, not the exe).
- From a VS Code terminal, clear the inherited Electron flag first, or the app crashes at
  start with "reading 'setPath'":
  `Remove-Item Env:ELECTRON_RUN_AS_NODE, Env:AG_MOCK, Env:AG_MOCK_FIXTURE, Env:AG_ENGINE_EXE -ErrorAction SilentlyContinue`
- Have to hand: demo key AG-DEMO-0001 (`shared/license/demo-keys.md`); the expired token
  (`tools/demo-tokens.txt`, git-ignored: paste it, never show it on the projector or commit it);
  a tampered token = AG-DEMO-0001's token with one character in the middle changed.
- Windows Security and Settings open on a second screen for 5.6.

## Steps

| # | Owner | Command / action (cwd) | Check |
|---|---|---|---|
| 5.1 | Frank | Wi-Fi OFF. `npm run dev` (cwd `desktop`), no mock variables | Window opens |
| 5.2 | Shakir | `Remove-Item $env:APPDATA\Antigravity\license.txt -ErrorAction SilentlyContinue`; close and restart the app | License screen shows |
| 5.3 | Shakir | Enter, in order: expired token, tampered token, AG-DEMO-0001 | "This key expired on ..."; tampered token rejected (manual 3.11 table); then main screen with "Start scan", footer shows licence id |
| 5.4 | Frank | Click "Start scan"; start a stopwatch | Phase messages in order: starting, host, backup, patch, software, protection, recovery, engine (manual 4.8); bar never sticks at ~4% |
| 5.5 | Tshedi | Watch for the Results screen; stop the stopwatch | Results in < 60 s non-elevated. Reference on Dev-1 (terminal, 28 Oct): host 0.5 s, backup 0.2 s, patch 0.2 s, software 1.0 s, protection 0.4 s, recovery 0.8 s, engine 0.5 s; total ~3.7 s |
| 5.6 | Everyone | Check each of the 5 cards against Windows Security / Settings | Agreement, or a bug list with owners. Known open item: Recovery shows "System Restore: Off" while restore points exist (manual 3.5 marks the registry method "verify"); check System Protection for C: |
| 5.7 | Frank | Click "Open one-page action plan (PDF)", then "Open full report" | PDF opens in Edge, exactly 1 page; HTML opens offline, colours correct |
| 5.8 | Frank | Click "Scan again" | Second run completes; `dir $env:LOCALAPPDATA\Antigravity\runs` shows exactly one folder |
| 5.9 | Schwan | Start a scan, click "Cancel" within 5 s. Then run the process check below | Error screen "Scan cancelled"; process check prints 0 and 0 |
| 5.10 | Frank | Close the app. Open an Administrator terminal, clear the env vars as above, repeat 5.1, 5.4-5.5 | More rows rated (Windows Backup, shadow copies, recovery tools, restore points); still < 60 s |
| 5.11 | Tshedi | Only after everyone agrees on 5.6, and after asking Shakir: `git tag v0.1-integrated; git push origin v0.1-integrated` (cwd repo root) | Tag on GitHub |

## 5.9 process check (cwd any, read-only)

```powershell
$p = Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='python.exe' OR Name='engine.exe'"
"collector left: " + @($p | Where-Object { $_.CommandLine -like '*collector.ps1*' }).Count
"engine left:    " + @($p | Where-Object { $_.CommandLine -like '*antigravity_engine*' -or $_.Name -eq 'engine.exe' }).Count
```

Both counts must be 0. Other powershell.exe processes (VS Code terminals) are not ours and are
not counted.

## After the run

- One line per step result in `docs/decisions.md` (date, brick, step, result).
- Delete `out\int\evidence-2026-10-28T07-38-00Z_93ab.json` (real evidence kept for Phase 5 only).
