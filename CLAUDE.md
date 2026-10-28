@.claude/academy.md

# Antigravity — Shakir's working rules (Brick B)

Personal file: git-ignored, not shared with the team.

## Project in one paragraph

Antigravity is a read-only, offline Windows cyber health check for South African SMMEs.
Pipeline: licence key → `collector.ps1` (PowerShell 5.1) writes `scan.json` →
`engine.exe` (Python) writes `report.json` + `report.html` + `action-plan.pdf` →
Electron/React UI shows red/amber/green results. The manual at `docs/manual.md` is the
source of truth. Cite its section numbers (e.g. "§3.4") instead of pasting its contents.
If the manual and code disagree, the manual is right until it is updated first.

## My scope (Brick B — Shakir)

I own and may edit:
- `collector/**`: collector entry script, `lib/`, `probes/`, `mocks/`, `tests/` (§3)
- `shared/contract/**` and `shared/fixtures/scan.*.json`: the data contract (§0, Appendix A)
- `shared/license/**`, `tools/issue-license.mjs`, `tools/security/**` (§3.11, §7.2)
- `desktop/src/main/license/**`: `verify.ts`, `verify.test.ts`, `store.ts` (§3.11)
- `installer/contract-check.ps1` (shared with Schwan, §6.3)

Do NOT edit other bricks' folders (`engine/`, `baseline/`, `desktop/src/renderer/`,
the rest of `desktop/src/main/`, `landing/`, `installer/` except contract-check). If a change
is needed there, stop and tell me who owns it.

Contract rule: `shared/contract/` is frozen after 16:00 Day 1. Any change after that needs
all four team members to agree first (§0.10). Never change it silently.

## Learning checkpoints: I must understand every line

Work on ONE work package at a time. Never start the next one without my "continue".

1. **Before coding.** Explain the plan in plain English: files, functions, manual section,
   risks. Wait for my approval.
2. **After coding.** Walk me through the diff function by function, in under 300 words
   (I will ask for more). Explicitly flag every registry read, cmdlet call, external exe,
   file write and crypto operation, and say why it is read-only/safe.
3. **Verification.** Give me the exact commands to run myself (do NOT run them for me) and
   the expected output. Then ask me 3 questions about failure, non-admin and edge-case
   behaviour. Wait for my answers and correct me.
4. **Commit.** Only after I say "verified", commit on `brick/collector` with a
   conventional message: `feat(collector): ...`, `fix(collector): ...`, `contract: ...`.
   Then suggest one line for `docs/pitch-notes.md` that captures what I learned.

Checkpoint depth:
- **Full (all 4 steps):** `lib/Common.ps1`, `lib/Allowlist.ps1`, `tests/Test-ReadOnly.ps1`,
  `probes/Protection.ps1`, `verify.ts`, `contract-check.ps1`.
- **Light (short walkthrough + I run the test):** the other probes, `Test-Collector.ps1`, `store.ts`.
- **Mechanical (just give me the test command):** mock files, fixtures, allowlist entries,
  generated `types.ts`.

## Work packages, in order

0. Contract: `scan.schema.json` (Appendix A.1), `types.ts`, fixtures (§0.7) + `scan.xss.json`
1. Skeleton: `collector.ps1`, `lib/Common.ps1`, `lib/Allowlist.ps1` (§3.2–§3.4, §3.8)
2. Guard rail: `tests/Test-ReadOnly.ps1` (§3.7)
3. Probes: Host, Protection, Patch, Software, Backup, Recovery (§3.5, §3.6)
4. Mocks + `tests/Test-Collector.ps1` (§3.10)
5. Licence: `verify.ts`, `verify.test.ts`, `store.ts` (§3.11). Can run alongside package 3
6. Integration: `-RunId`, `AG-PHASE:` markers, `installer/contract-check.ps1` (§3.3, §4.8, §6.3)

## Agent routing (Academy)

- **Socrates must review** any probe, `Allowlist.ps1`, `Test-ReadOnly.ps1`, `verify.ts` or
  contract change BEFORE checkpoint 2.
- Aristotle builds anything needing reasoning (probes, `Common.ps1`, `verify.ts`).
- Diogenes does fully specified mechanical work (fixtures, mocks, schema transcription).
- Thales searches the manual and repo.

## Hard safety rules (never break these)

The collector is READ-ONLY (§3.7). In code AND when running commands on this machine:
- Never run or write `Set-*`, `New-*` (except allow-listed `New-Object` COM reads), `Remove-*`,
  `Add-*`, `Clear-*`, `Enable-*`, `Disable-*`, `Start-*`, `Stop-*`, `Restart-*`, `Install-*`,
  `Uninstall-*`, `Update-*`, `Register-*`, `Invoke-WebRequest`, `Invoke-RestMethod`.
- Never use `Win32_Product`, `vssadmin`, `wbadmin start`, `manage-bde`, `reagentc /enable|/disable`,
  `Checkpoint-Computer`, `bcdedit`. The only external exe allowed is `reagentc.exe /info`.
- Never change Defender, BitLocker, services, registry, execution policy or firewall settings,
  even "to test". I make any test state changes by hand (§3.9).
- No network calls, no `-EncodedCommand`, no `-WindowStyle Hidden`.
- POPIA: output never contains usernames, file paths, IPs, MACs, serial numbers or raw
  hostnames. Error strings use fixed messages with no paths (§3.4 rule 4).
- Never read, print, copy or commit `%USERPROFILE%\.antigravity-private.pem`. Never run
  `node tools/issue-license.mjs keygen`: it would overwrite the real signing key.
- Never commit `tools/demo-tokens.txt`, real scan output, `.offline/` or `node_modules/`.

## PowerShell 5.1 rules (§1.4, §3.8)

- Always `powershell.exe` (5.1), never `pwsh`. Save `.ps1` files as UTF-8 with BOM.
- `ConvertTo-Json -InputObject $x -Depth 8`; wrap arrays in `@()`; dates via `ConvertTo-IsoUtc`;
  write JSON with `[IO.File]::WriteAllText(..., (New-Object Text.UTF8Encoding $false))` (no BOM).
- Probes call `Read-Ag*` readers in `Common.ps1`, never system cmdlets directly for scored values,
  so mocks can override them (§3.10).
- Every probe goes through `Invoke-Probe`: known precondition → `[AgUnavailable]` → `unavailable`;
  anything else → `failed`. Admin-only fields inside a readable section → `$null`, section stays `ok`.

## Check commands (cwd: repo root unless stated)

    powershell -NoProfile -ExecutionPolicy Bypass -File collector\tests\Test-ReadOnly.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File collector\tests\Test-Collector.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -Only Protection -DryRun
    powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -OutputPath out\dev\scan.json
    engine\.venv\Scripts\python engine\tools\validate.py scan out\dev\scan.json
    powershell -NoProfile -ExecutionPolicy Bypass -File installer\contract-check.ps1
    # cwd: desktop
    npm run test

## Git

- Work only on `brick/collector` (contract changes on `contract/<topic>`). Never commit to `main`,
  never force-push. Rebase on main with `git pull --rebase origin main` before a PR.
- Commit only after checkpoint 4. Paste isolation-test output into PR descriptions.