@.claude/academy.md

# Antigravity — Shakir's working rules (Brick B)

Personal file: git-ignored, not shared with the team.

## 1. Project in one paragraph

Antigravity is a read-only, offline Windows cyber health check for South African SMMEs.
Pipeline: licence key → `collector.ps1` (PowerShell 5.1) writes `scan.json` →
`engine.exe` (Python) writes `report.json`, `report.html`, `action-plan.pdf` and `evidence.json` →
Electron/React UI shows red/amber/green results. A third party can check `evidence.json` with
`engine.exe --verify`. The manual at `docs/antigravity_manual_v1.1.md` (v1.1) is the source of truth. Cite its
section numbers (e.g. "§3.4") instead of pasting its contents. If the manual and the code
disagree, stop and tell me; the manual is updated first, then the code.

## 2. My scope (Brick B)

May edit:
- `collector/**` (§3)
- `shared/contract/**` and `shared/fixtures/scan.*.json` (§0, Appendix A, incl. A.3 evidence schema)
- `shared/license/**`, `tools/issue-license.mjs`, `tools/security/**` (§3.11, §7.2)
- `desktop/src/main/license/**` (§3.11)
- `installer/contract-check.ps1` (shared with Schwan, §6.3)
- `docs/briefs/**` (phase briefs, see §5 below)

Must NOT edit any other folder. If a change is needed elsewhere, stop and tell me who owns it.
`shared/contract/` is frozen after 16:00 Day 1; after that, never change it without my explicit
instruction (all four team members must agree first, §0.10).

## 3. Phases

Work happens in numbered phases. **Never start a phase until I type `Start Phase N`.**
Never start the next phase on your own, even if the current one finished early.

| Phase | Deliverable | Manual |
|---|---|---|
| 0 | Contract: `scan.schema.json`, `evidence.schema.json`, `types.ts`, fixtures incl. `scan.xss.json` | §0.5–§0.7, App. A |
| 1 | Skeleton: `collector.ps1`, `lib/Common.ps1` (incl. `Read-Ag*` readers), `lib/Allowlist.ps1` | §3.2–§3.4, §3.8 |
| 2 | Read-only guard: `tests/Test-ReadOnly.ps1` | §3.7 |
| 3 | Probes A: Host, Protection | §3.5, §3.6 |
| 4 | Probes B: Patch, Software, Backup, Recovery | §3.5, §3.6 |
| 5 | Mocks + `tests/Test-Collector.ps1` covering every mock case | §3.10 |
| 6 | Licence: `verify.ts`, `verify.test.ts`, `store.ts` | §3.11 |
| 7 | Integration: `-RunId`, `AG-PHASE:` markers, `installer/contract-check.ps1` | §3.3, §4.8, §6.3 |

If I say `Start Phase N` and an earlier phase isn't finished, say so and wait.

## 4. How every phase runs (test-first)

1. **Plan (stop and wait).** Plato posts a short plan: files, functions, manual sections,
   the list of tests that will prove the phase works, and any decision needing my input.
   Wait for my `Go`.
2. **Tests first.** Write the tests before any implementation. Run them and show me they
   FAIL for the right reason (e.g. "function not found", not a typo). Paste the failing output.
3. **Implement** the smallest code that makes the tests pass. Do not change a test to make it
   pass unless the test itself is wrong; if so, say why in the brief.
4. **Review.** Socrates reviews any phase that touches the contract, a probe, `Allowlist.ps1`,
   `Test-ReadOnly.ps1`, `verify.ts` or `contract-check.ps1`. Every Socrates question gets an answer.
5. **Gate.** Run ALL tests for this phase AND all earlier phases, plus `Test-ReadOnly.ps1` from
   Phase 2 onward. The phase ends only when every one passes. If any fail after two fix
   attempts, stop and tell me; never mark a phase done with a failing or skipped test.
6. **Brief** (§5), then stop. Do not commit until I reply `Verified`.
7. **Commit** on `brick/collector` (contract work: `contract/<topic>`), conventional message,
   e.g. `feat(collector): add Host and Protection probes`. Never push unless I ask.

## 5. Phase brief (required after every phase)

Write it to `docs/briefs/phase-N.md` and post the same text in chat. Plain English, no
unexplained jargon (explain any technical term in a few words the first time), but technically
precise. Sections, in this order:

1. **What was built.** Each file created or changed, and in 1–3 sentences what it does and why.
2. **How it works.** The flow in plain steps. For every registry read, cmdlet, external program,
   file write or crypto operation, say what it touches and why it is safe/read-only.
3. **Tests written.** A table: test name | what it checks | why it matters.
4. **Test results.** Pass/fail counts and the key lines of real output (not paraphrased).
   Include the failing output from step 2 of §4 as proof the tests came first.
5. **Run it yourself.** Exact commands, each with its working folder, and what I should see
   if it works and what it means if I see something else.
6. **Decisions and limits.** Anything assumed, deferred, or not covered, and open questions.
7. **Pitch line.** One sentence for `docs/pitch-notes.md`.

## 6. Hard safety rules (never break, in code or in commands run on this PC)

- The collector is READ-ONLY (§3.7). Never run or write `Set-*`, `New-*` (except allow-listed
  `New-Object` COM reads), `Remove-*`, `Add-*`, `Clear-*`, `Enable-*`, `Disable-*`, `Start-*`,
  `Stop-*`, `Restart-*`, `Install-*`, `Uninstall-*`, `Update-*`, `Register-*`,
  `Invoke-WebRequest`, `Invoke-RestMethod`.
- Never use `Win32_Product`, `vssadmin`, `wbadmin start`, `manage-bde`, `reagentc /enable|/disable`,
  `Checkpoint-Computer`, `bcdedit`. Only external exe allowed: `reagentc.exe /info`.
- Never change Defender, BitLocker, services, registry, execution policy or firewall settings,
  not even "to test". Use mocks (§3.10); I make real state changes by hand.
- No network calls, no `-EncodedCommand`, no `-WindowStyle Hidden`.
- POPIA: output never contains usernames, file paths, IPs, MACs, serial numbers or raw
  hostnames. Error messages are fixed text with no paths (§3.4 rule 4).
- Never read, print, copy or commit `%USERPROFILE%\.antigravity-private.pem`. Never run
  `node tools/issue-license.mjs keygen`.
- Never commit `tools/demo-tokens.txt`, real scan output, `out/`, `.offline/` or `node_modules/`.
- No new dependencies of any kind without asking me first.

## 7. PowerShell 5.1 rules (§1.4, §3.8)

- Always `powershell.exe` (5.1), never `pwsh`. Save `.ps1` files as UTF-8 with BOM.
- `ConvertTo-Json -InputObject $x -Depth 8`; wrap arrays in `@()`; dates via `ConvertTo-IsoUtc`;
  write JSON with `[IO.File]::WriteAllText(..., (New-Object Text.UTF8Encoding $false))`.
- Probes call `Read-Ag*` readers, never system cmdlets directly for scored values (§3.10).
- Every probe goes through `Invoke-Probe`: known precondition → `unavailable`; anything else →
  `failed`. Admin-only fields inside a readable section → `$null`, section stays `ok`.

## 8. Agent behaviour

- Plato plans, routes and reviews; follow `.claude/academy.md` for routing and commissions.
  Commissions point at manual sections and file paths, not pasted text.
- Stop and ask (aporia) instead of guessing on anything in §2, §3 or §6.
- Keep `.claude/agora.md` cleared at the end of each phase.
- Keep chat updates short during a phase; save detail for the brief.