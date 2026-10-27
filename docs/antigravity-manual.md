# Team Antigravity — Build & Integration Manual
**HackSecure 2026 · Track 3: SMME Cyber Protection** · Consolidated edition, 25 October 2026

| Brick | Owner | Builds | Section |
|---|---|---|---|
| **A** | Tshedi Sefula (lead) | Assessment engine, baseline, PyInstaller | §2 |
| **B** | Shakir Alexander | Windows collector, licence verification, data contract | §3 |
| **C** | Frank Yamba | Electron/React UI, reports design, landing page, demo | §4 |
| **D** | Schwan Lungwangau | Main-process wiring, installer, clean-machine tests | §5 |

**About this edition**
- This single file replaces the six section files (§0–§1, §2–§3, §4–§5, §6–§7, §8, §9–§10). Every change those files asked to be made to earlier sections has been applied; Appendix H lists them.
- The HackSecure 2026 Official Programme and the Idea Canvas were not available while this manual was written. Programme times come from the team's brief; anything marked *(confirm against programme)* or *(confirm against the Idea Canvas)* must be checked before printing.
- Keep it current with the rules in the **Manual maintenance note** at the end.

---

## Table of Contents

- [§0 How to read this manual](#0-how-to-read-this-manual)
  - [0.1 The brick metaphor](#01-the-brick-metaphor)
  - [0.2 The isolation-test rule](#02-the-isolation-test-rule)
  - [0.3 Definition of done, per brick](#03-definition-of-done-per-brick)
  - [0.4 Tags and conventions](#04-tags-and-conventions)
  - [0.5 Input contract: collector → engine](#05-input-contract-collector--engine)
  - [0.6 Input contract: field-by-field table](#06-input-contract-field-by-field-table)
  - [0.7 Example payloads](#07-example-payloads)
  - [0.8 Output contract: engine → UI/PDF](#08-output-contract-engine--uipdf)
  - [0.9 "unavailable" vs "failed"](#09-unavailable-vs-failed)
  - [0.10 Contract change procedure](#010-contract-change-procedure)
- [§1 Environment & prerequisites](#1-environment--prerequisites)
  - [1.1 Version matrix](#11-version-matrix)
  - [1.2 Install steps (per machine)](#12-install-steps-per-machine)
  - [1.3 Package manager decision: npm](#13-package-manager-decision-npm)
  - [1.4 PowerShell 5.1 and execution policy](#14-powershell-51-and-execution-policy)
  - [1.5 Download-everything-before-you-travel checklist](#15-download-everything-before-you-travel-checklist)
  - [1.6 Electron offline: ELECTRON_MIRROR and caches](#16-electron-offline-electron_mirror-and-caches)
  - [1.7 Monorepo folder tree](#17-monorepo-folder-tree)
  - [1.8 Environments and isolation](#18-environments-and-isolation)
  - [1.9 Git workflow](#19-git-workflow)
  - [1.10 Dependency manifests](#110-dependency-manifests)
- [§2 Brick A: Assessment Engine (Tshedi)](#2-brick-a-assessment-engine-tshedi)
  - [2.1 Folder layout](#21-folder-layout)
  - [2.2 Venv and dependencies](#22-venv-and-dependencies)
  - [2.3 Module breakdown](#23-module-breakdown)
  - [2.4 How the engine consumes the contract](#24-how-the-engine-consumes-the-contract)
  - [2.5 Scoring rules per category](#25-scoring-rules-per-category)
  - [2.6 Aggregation, weighting and top-3](#26-aggregation-weighting-and-top-3)
  - [2.7 Keeping "unavailable" separate from "failed"](#27-keeping-unavailable-separate-from-failed)
  - [2.8 Baseline JSON schema](#28-baseline-json-schema)
  - [2.9 Fix catalogue](#29-fix-catalogue)
  - [2.10 Unit tests](#210-unit-tests)
  - [2.11 Running the engine standalone](#211-running-the-engine-standalone)
  - [2.12 PyInstaller build and no-Python verification](#212-pyinstaller-build-and-no-python-verification)
  - [2.13 Brick A is done when…](#213-brick-a-is-done-when)
- [§3 Brick B: Windows Collector (Shakir)](#3-brick-b-windows-collector-shakir)
  - [3.1 Folder layout](#31-folder-layout)
  - [3.2 Script structure: one entry script + dot-sourced probes](#32-script-structure-one-entry-script--dot-sourced-probes)
  - [3.3 Parameters: -OutputPath, -DryRun, -Only, -MockFile, -RunId](#33-parameters--outputpath--dryrun--only--mockfile--runid)
  - [3.4 The probe wrapper](#34-the-probe-wrapper)
  - [3.5 Query reference per category](#35-query-reference-per-category)
  - [3.6 Graceful "not available" handling](#36-graceful-not-available-handling)
  - [3.7 Read-only guarantee](#37-read-only-guarantee)
  - [3.8 Writing scan.json correctly in PowerShell 5.1](#38-writing-scanjson-correctly-in-powershell-51)
  - [3.9 Testing on two dev machines](#39-testing-on-two-dev-machines)
  - [3.10 Faking missing data](#310-faking-missing-data)
  - [3.11 License token verification](#311-license-token-verification)
  - [3.12 Execution policy and code signing](#312-execution-policy-and-code-signing)
  - [3.13 Brick B is done when…](#313-brick-b-is-done-when)
- [§4 Brick C: Electron/React Frontend & Reports (Frank)](#4-brick-c-electronreact-frontend--reports-frank)
  - [4.1 Folder layout](#41-folder-layout)
  - [4.2 package.json](#42-packagejson)
  - [4.3 Tailwind v4 + shadcn/ui setup](#43-tailwind-v4--shadcnui-setup)
  - [4.4 Main / preload / renderer split](#44-main--preload--renderer-split)
  - [4.5 How the app runs the collector and engine](#45-how-the-app-runs-the-collector-and-engine)
  - [4.6 IPC contract](#46-ipc-contract)
  - [4.7 Exact spawn calls](#47-exact-spawn-calls)
  - [4.8 Progress model](#48-progress-model)
  - [4.9 Screens](#49-screens)
  - [4.10 HTML report template](#410-html-report-template)
  - [4.11 PDF one-pager](#411-pdf-one-pager)
  - [4.12 Mock data for UI development](#412-mock-data-for-ui-development)
  - [4.13 Landing page and Vercel deploy](#413-landing-page-and-vercel-deploy)
  - [4.14 Brick C is done when…](#414-brick-c-is-done-when)
- [§5 Brick D: Packaging & Deployment (Schwan)](#5-brick-d-packaging--deployment-schwan)
  - [5.1 Folder layout](#51-folder-layout)
  - [5.2 electron-builder.yml, field by field](#52-electron-builderyml-field-by-field)
  - [5.3 NSIS installer settings](#53-nsis-installer-settings)
  - [5.4 Bundling the engine and collector as extraResources](#54-bundling-the-engine-and-collector-as-extraresources)
  - [5.5 Path resolution: dev vs packaged](#55-path-resolution-dev-vs-packaged)
  - [5.6 Startup sequence](#56-startup-sequence)
  - [5.7 Code signing and SmartScreen](#57-code-signing-and-smartscreen)
  - [5.8 Building the installer](#58-building-the-installer)
  - [5.9 Clean-Windows-VM test](#59-clean-windows-vm-test)
  - [5.10 Brick D is done when…](#510-brick-d-is-done-when)
- [§6 Integration sequence](#6-integration-sequence)
  - [6.1 Before you start](#61-before-you-start)
  - [6.2 Phase 1 — Merge the four bricks](#62-phase-1--merge-the-four-bricks)
  - [6.3 Phase 2 — Wire collector → engine](#63-phase-2--wire-collector--engine)
  - [6.4 Phase 3 — Wire engine → UI](#64-phase-3--wire-engine--ui)
  - [6.5 Phase 4 — Wire UI → installer](#65-phase-4--wire-ui--installer)
  - [6.6 Phase 5 — First full end-to-end dev-mode run](#66-phase-5--first-full-end-to-end-dev-mode-run)
  - [6.7 Phase 6 — First installer](#67-phase-6--first-installer)
  - [6.8 Troubleshooting](#68-troubleshooting)
- [§7 Cybersecurity test plan](#7-cybersecurity-test-plan)
  - [7.1 How to run this plan](#71-how-to-run-this-plan)
  - [7.2 Test tooling (prepare at home)](#72-test-tooling-prepare-at-home)
  - [7.3 Read-only verification (RO)](#73-read-only-verification-ro)
  - [7.4 License security (LIC)](#74-license-security-lic)
  - [7.5 Data privacy / POPIA (PRV)](#75-data-privacy--popia-prv)
  - [7.6 Report integrity (RPT)](#76-report-integrity-rpt)
  - [7.7 Least privilege (LP)](#77-least-privilege-lp)
  - [7.8 Tamper resistance (TMP)](#78-tamper-resistance-tmp)
  - [7.9 Installer security (INS)](#79-installer-security-ins)
  - [7.10 Threat model](#710-threat-model)
- [§8 Programme-aware build timeline](#8-programme-aware-build-timeline)
  - [8.1 Read this first: sources, conflicts and adjustments](#81-read-this-first-sources-conflicts-and-adjustments)
  - [8.2 The real hacking budget](#82-the-real-hacking-budget)
  - [8.3 Pre-travel plan and per-member estimates](#83-pre-travel-plan-and-per-member-estimates)
  - [8.4 Day 1 timeline](#84-day-1-timeline)
  - [8.5 Overnight rest rota](#85-overnight-rest-rota)
  - [8.6 Day 2 timeline](#86-day-2-timeline)
  - [8.7 Release-candidate rule for Day 2](#87-release-candidate-rule-for-day-2)
  - [8.8 "If we are behind at T, we cut X" ladder](#88-if-we-are-behind-at-t-we-cut-x-ladder)
  - [8.9 Decision rights and ticket handling](#89-decision-rights-and-ticket-handling)
- [§9 Demo rehearsal & fallback](#9-demo-rehearsal--fallback)
  - [9.1 Roles](#91-roles)
  - [9.2 Slot assumptions](#92-slot-assumptions)
  - [9.3 Demo laptop layout](#93-demo-laptop-layout)
  - [9.4 The 5-minute demo script](#94-the-5-minute-demo-script)
  - [9.5 Fallback triggers](#95-fallback-triggers)
  - [9.6 Fallback artefacts: where they live and how to launch them](#96-fallback-artefacts-where-they-live-and-how-to-launch-them)
  - [9.7 Pre-pitch checklist](#97-pre-pitch-checklist)
  - [9.8 Q&A preparation](#98-qa-preparation)
  - [9.9 Pitch-slot run sheet (one page)](#99-pitch-slot-run-sheet-one-page)
- [§10 Appendices](#10-appendices)
  - [Appendix A — Shared JSON schemas](#appendix-a--shared-json-schemas)
  - [Appendix B — Pinned dependency manifests](#appendix-b--pinned-dependency-manifests)
  - [Appendix C — Full annotated folder tree](#appendix-c--full-annotated-folder-tree)
  - [Appendix D — Git branch / PR checklist](#appendix-d--git-branch--pr-checklist)
  - [Appendix E — Definition-of-done one-pagers](#appendix-e--definition-of-done-one-pagers)
  - [Appendix F — Glossary](#appendix-f--glossary)
  - [Appendix G — One-page timeline (print and tape to the table)](#appendix-g--one-page-timeline-print-and-tape-to-the-table)
  - [Appendix H — Change log (folded into this edition)](#appendix-h--change-log-folded-into-this-edition)
- [Manual maintenance note](#manual-maintenance-note)

---

## §0 How to read this manual

### 0.1 The brick metaphor

The product is four bricks joined by two studs (the contracts). Each person owns one brick; nobody edits another brick's folder without asking its owner.

| Brick | Owner | Folder(s) | Consumes | Produces |
|---|---|---|---|---|
| **A — Assessment Engine** | Tshedi Sefula | `/engine`, `/baseline` | `scan.json` + baseline | `report.json` (§0.8), `report.html`, `action-plan.pdf` |
| **B — Collector & License** | Shakir Alexander | `/collector`, `/shared/contract`, `/desktop/src/main/license` | Windows (read-only) | `scan.json` (§0.5) |
| **C — Product & Frontend** | Frank Yamba | `/desktop/src/renderer`, `/landing` | `report.json` | Screens, demo |
| **D — Packaging & Deployment** | Schwan Lungwangau | `/installer`, `/desktop/electron-builder.yml`, `/desktop/src/main/pipeline` | All three bricks' build outputs | `Antigravity-Setup-x.y.z.exe` |

Pipeline (wired by D in §5; spawn calls in §4.7):

```
[License key] → Electron main → powershell.exe collector.ps1 → scan.json
             → engine.exe --in scan.json --out <dir> → report.json + report.html + action-plan.pdf
             → React renderer reads report.json
```

Rule: **bricks talk only through files that match the contracts.** No brick imports another brick's code.

### 0.2 The isolation-test rule

1. Every brick ships a test that runs with **no other brick present**.
2. The test feeds the brick fixtures from `/shared/fixtures/` (the payloads in §0.7) — never live output from another brick.
3. A brick may not be merged to `main` until its isolation test passes on the owner's machine **and** in a second team member's checkout.
4. If integration breaks, first re-run each brick's isolation test. The brick that fails owns the bug; if all pass, the contract is wrong — go to §0.10.

| Brick | Isolation test command | Working dir | Passes when |
|---|---|---|---|
| A | `.venv\Scripts\python -m pytest -q` | `/engine` | All fixtures produce expected RAG per category |
| B | `powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-Collector.ps1` | `/collector` | Output validates against `scan.schema.json`; zero write operations in script (static check) |
| C | `npm run test` | `/desktop` | Renderer renders all 3 fixture `report.json` files without errors |
| D | `npm run dist && ..\installer\smoke-test.ps1` | `/desktop` | Installer installs on clean VM, app launches, demo scan completes |

### 0.3 Definition of done, per brick

A brick is **done** when every box is ticked. Full per-brick checklists with due times: Appendix E.

**A — Engine [MVP]**
- [ ] `engine.exe --in scan.json --out <dir>` produces `report.json`, `report.html`, `action-plan.pdf` in < 5 s.
- [ ] Output validates against `/shared/contract/report.schema.json`.
- [ ] Baseline in `/baseline/software-baseline.json` with ≥ 10 common SMME apps.
- [ ] PyInstaller one-folder build runs on a machine with no Python installed.
- [ ] Malformed input → exit code 2 + `report.json` with every category `failed`; never a crash dialog.

**B — Collector & License [MVP]**
- [ ] `collector.ps1` runs on PowerShell 5.1, non-admin and admin, finishes in < 20 s.
- [ ] Output validates against `/shared/contract/scan.schema.json`.
- [ ] Uses only `Get-*` cmdlets, registry reads, and read-only CLI queries. No `Set-*`, `New-*`, `Remove-*`, `Enable-*`, `Start-*`, file writes outside the output path.
- [ ] Every section returns `status` of `ok`, `unavailable` or `failed` — the script never throws to the caller.
- [ ] License: Ed25519-signed token verified locally in Electron main; 3 demo keys issued and tested; invalid/expired key shows a clear error.

**C — Frontend [MVP]**
- [ ] Screens: license entry → scanning (progress) → results (5 category cards) → "Open PDF".
- [ ] Renders all statuses including `unavailable` and `failed` (§0.9).
- [ ] Landing page deployed to Vercel with download link + demo key request instructions.
- [ ] HTML report and PDF one-pager design and wording handed to Tshedi (§4.10–§4.11).
- [ ] 5-minute demo script (§9.4) rehearsed twice.

**D — Packaging [MVP]**
- [ ] NSIS installer bundles Electron app, `collector.ps1`, `engine/` folder, baseline.
- [ ] Clean Windows 11 VM test: install → enter key → scan → report, with **network disabled**.
- [ ] Installer + checksum uploaded for submission before 11:30 Day 2.

### 0.4 Tags and conventions

| Tag | Meaning |
|---|---|
| **[MVP]** | Must exist at 11:45 Day 2 submission. |
| **[STRETCH]** | Only after all MVP bricks are integrated and demo-tested. |
| **Default:** | An open decision with our chosen answer + rationale. Change only by team agreement. |
| `§n.m` | Cross-reference — go there instead of re-reading an explanation here. |

Every command block starts with a comment stating the working directory, e.g. `# cwd: antigravity/engine`. Paths are relative to the repo root `antigravity/`.

### 0.5 Input contract: collector → engine

- **File:** `scan.json`, UTF-8, no BOM. Written by the collector to `%LOCALAPPDATA%\Antigravity\runs\<run_id>\scan.json`.
- **Schema:** `/shared/contract/scan.schema.json` (JSON Schema draft 2020-12). TypeScript types generated into `/shared/contract/types.ts`; Python mirrors in `/engine/antigravity_engine/contract.py`.
- **Version:** `schema_version` follows semver. Engine rejects a different **major** version.
- **POPIA-minimal:** no usernames, no file names, no IP/MAC addresses, no serial numbers. Hostname is stored only as a salted SHA-256 hash. Nothing leaves the machine.

Annotated contract (comments for reading only — real files are strict JSON):

```jsonc
{
  "schema_version": "1.0.0",            // semver; engine rejects other majors
  "run_id": "2026-11-14T16-42-07Z_7f3a", // UTC timestamp + 4 hex; also the run folder name
  "collected_at": "2026-11-14T16:42:07Z",// ISO-8601 UTC, when collection finished
  "collector_version": "0.1.0",          // collector.ps1 $Version
  "duration_ms": 8420,                   // total collection time; must stay < 60000

  "host": {
    "hostname_hash": "sha256:9c1e…",     // salted hash — never the raw hostname
    "os_caption": "Microsoft Windows 11 Pro",
    "os_build": "22631",                 // CurrentBuild from registry
    "os_edition": "Professional",        // EditionID; "Core" = Home (no BitLocker mgmt)
    "is_admin": true,                    // elevated? decides several "unavailable"s
    "ps_version": "5.1.22621.4391"
  },

  "backup": {                            // → category 1: Backup evidence
    "status": "ok",                      // ok | unavailable | failed  (§0.9)
    "error": null,                       // string when status != ok
    "file_history_enabled": true,        // registry: HKCU\...\FileHistory
    "file_history_last_backup": "2026-11-13T22:00:00Z", // null if never
    "windows_backup_last_success": null, // wbadmin get versions (admin) — null if none/unknown
    "onedrive_kfm_folders": ["Desktop","Documents"], // Known Folder Move redirection
    "shadow_copy_count": 3,              // vssadmin list shadows (admin); null if not admin
    "third_party_agents": ["Veeam Agent"]// matched from installed services list
  },

  "patch": {                             // → category 2: Patch status
    "status": "ok",
    "error": null,
    "hotfix_count": 14,
    "latest_hotfix_installed_on": "2026-11-05", // max InstalledOn from Get-HotFix
    "days_since_latest_hotfix": 9,       // collector computes; engine re-checks
    "hotfixes": [                        // newest 10 only (keep payload small)
      { "kb": "KB5044285", "installed_on": "2026-11-05" }
    ],
    "pending_reboot": false              // RebootRequired registry keys
  },

  "software": {                          // → category 3: Outdated software
    "status": "ok",
    "error": null,
    "installed": [                       // HKLM + HKCU Uninstall keys, deduped
      { "name": "Google Chrome", "version": "130.0.6723.117", "publisher": "Google LLC" }
    ]
  },

  "protection": {                        // → category 4: Ransomware protections
    "bitlocker": {
      "status": "ok",                    // unavailable when not admin or Home edition
      "error": null,
      "os_volume_protection": "on",      // on | off | null
      "os_volume_encryption_pct": 100,
      "encryption_method": "XtsAes128"
    },
    "defender": {
      "status": "ok",
      "error": null,
      "antivirus_enabled": true,         // Get-MpComputerStatus.AntivirusEnabled
      "realtime_enabled": true,          // .RealTimeProtectionEnabled
      "tamper_protected": true,          // .IsTamperProtected
      "signature_age_days": 0,           // .AntivirusSignatureAge
      "third_party_av": null             // SecurityCenter2 product name if Defender is passive
    },
    "cfa": {
      "status": "ok",
      "error": null,
      "mode": "enabled"                  // enabled | disabled | audit  (Get-MpPreference)
    },
    "asr": {
      "status": "ok",
      "error": null,
      "rules": [                         // Get-MpPreference AttackSurfaceReductionRules_*
        { "id": "d4f940ab-401b-4efc-aadc-ad5f3c50688a", "action": "block" } // block|audit|warn|off
      ]
    }
  },

  "recovery": {                          // → category 5: Recovery readiness
    "status": "ok",
    "error": null,
    "winre_enabled": true,               // reagentc /info (admin) — null if not admin
    "system_restore_enabled": true,
    "restore_point_count": 2,            // Get-ComputerRestorePoint (admin)
    "latest_restore_point": "2026-11-10T09:12:00Z"
  }
}
```

### 0.6 Input contract: field-by-field table

Category key: **1** Backup · **2** Patch · **3** Software · **4** Protections · **5** Recovery · **—** metadata.

| Field | Type | Req? | Example | Meaning | Cat |
|---|---|---|---|---|---|
| `schema_version` | string (semver) | ✅ | `"1.0.0"` | Contract version | — |
| `run_id` | string | ✅ | `"2026-11-14T16-42-07Z_7f3a"` | Unique run id, folder name | — |
| `collected_at` | string (ISO UTC) | ✅ | `"2026-11-14T16:42:07Z"` | Collection end time; "now" for all age maths | — |
| `collector_version` | string | ✅ | `"0.1.0"` | Collector build | — |
| `duration_ms` | integer | ✅ | `8420` | Collection time | — |
| `host.hostname_hash` | string | ✅ | `"sha256:9c1e…"` | Salted hash, report display only | — |
| `host.os_caption` | string | ✅ | `"Microsoft Windows 11 Pro"` | OS name shown in report | 2 |
| `host.os_build` | string | ✅ | `"22631"` | Build number; flags EOL builds | 2 |
| `host.os_edition` | string | ✅ | `"Professional"` | `Core` = Home → BitLocker explanation changes | 4 |
| `host.is_admin` | boolean | ✅ | `true` | Explains `unavailable` fields | all |
| `host.ps_version` | string | ✅ | `"5.1.22621.4391"` | Diagnostics | — |
| `backup.status` | enum | ✅ | `"ok"` | §0.9 | 1 |
| `backup.error` | string\|null | ✅ | `null` | Reason when not ok | 1 |
| `backup.file_history_enabled` | boolean\|null | ✅ | `true` | File History on | 1 |
| `backup.file_history_last_backup` | string\|null | ✅ | `"2026-11-13T22:00:00Z"` | Last File History run | 1 |
| `backup.windows_backup_last_success` | string\|null | ✅ | `null` | Last wbadmin success | 1 |
| `backup.onedrive_kfm_folders` | string[] | ✅ | `["Desktop","Documents"]` | Folders synced to OneDrive | 1 |
| `backup.shadow_copy_count` | integer\|null | ✅ | `3` | VSS snapshots | 1, 5 |
| `backup.third_party_agents` | string[] | ✅ | `["Veeam Agent"]` | Known backup services detected | 1 |
| `patch.status` / `.error` | enum / string\|null | ✅ | `"ok"` / `null` | §0.9 | 2 |
| `patch.hotfix_count` | integer | ✅ | `14` | Installed hotfixes | 2 |
| `patch.latest_hotfix_installed_on` | string (date)\|null | ✅ | `"2026-11-05"` | Newest hotfix date | 2 |
| `patch.days_since_latest_hotfix` | integer\|null | ✅ | `9` | Drives 30/60-day heuristic | 2 |
| `patch.hotfixes[]` | object[] (`kb`, `installed_on`) | ✅ | see §0.5 | Evidence rows (max 10) | 2 |
| `patch.pending_reboot` | boolean\|null | ✅ | `false` | Updates waiting on restart | 2 |
| `software.status` / `.error` | enum / string\|null | ✅ | `"ok"` | §0.9 | 3 |
| `software.installed[]` | object[] (`name`, `version`, `publisher`) | ✅ | see §0.5 | Matched against baseline | 3 |
| `protection.bitlocker.status` | enum | ✅ | `"unavailable"` | §0.9 | 4 |
| `protection.bitlocker.os_volume_protection` | `"on"`\|`"off"`\|null | ✅ | `"on"` | C: protection | 4 |
| `protection.bitlocker.os_volume_encryption_pct` | integer\|null | ✅ | `100` | Encryption progress | 4 |
| `protection.bitlocker.encryption_method` | string\|null | ⬜ | `"XtsAes128"` | Evidence only | 4 |
| `protection.defender.antivirus_enabled` | boolean\|null | ✅ | `true` | AV on | 4 |
| `protection.defender.realtime_enabled` | boolean\|null | ✅ | `true` | Real-time on | 4 |
| `protection.defender.tamper_protected` | boolean\|null | ✅ | `true` | Tamper Protection on | 4 |
| `protection.defender.signature_age_days` | integer\|null | ✅ | `0` | Definitions age | 4 |
| `protection.defender.third_party_av` | string\|null | ⬜ | `"ESET Security"` | Another AV is primary | 4 |
| `protection.cfa.mode` | enum\|null | ✅ | `"enabled"` | Controlled Folder Access | 4 |
| `protection.asr.rules[]` | object[] (`id`, `action`) | ✅ | see §0.5 | ASR rule states | 4 |
| `recovery.status` / `.error` | enum / string\|null | ✅ | `"ok"` | §0.9 | 5 |
| `recovery.winre_enabled` | boolean\|null | ✅ | `true` | Windows RE available | 5 |
| `recovery.system_restore_enabled` | boolean\|null | ✅ | `true` | System Restore on for C: | 5 |
| `recovery.restore_point_count` | integer\|null | ✅ | `2` | Restore points present | 5 |
| `recovery.latest_restore_point` | string\|null | ✅ | `"2026-11-10T09:12:00Z"` | Newest restore point | 5 |

"Required" means the **key must be present**; the value may be `null` where the type allows. Unknown extra keys are ignored by the engine (forward-compatible).

### 0.7 Example payloads

Save each as `/shared/fixtures/scan.<name>.json`. These are the only inputs bricks A and C test against (§0.2).

**Fixture 1 — `scan.healthy.json`** (expected: all green)

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-11-14T16-42-07Z_0001",
  "collected_at": "2026-11-14T16:42:07Z",
  "collector_version": "0.1.0",
  "duration_ms": 8420,
  "host": { "hostname_hash": "sha256:1111", "os_caption": "Microsoft Windows 11 Pro", "os_build": "22631", "os_edition": "Professional", "is_admin": true, "ps_version": "5.1.22621.4391" },
  "backup": { "status": "ok", "error": null, "file_history_enabled": true, "file_history_last_backup": "2026-11-13T22:00:00Z", "windows_backup_last_success": null, "onedrive_kfm_folders": ["Desktop", "Documents", "Pictures"], "shadow_copy_count": 3, "third_party_agents": [] },
  "patch": { "status": "ok", "error": null, "hotfix_count": 14, "latest_hotfix_installed_on": "2026-11-05", "days_since_latest_hotfix": 9, "hotfixes": [ { "kb": "KB5044285", "installed_on": "2026-11-05" }, { "kb": "KB5043080", "installed_on": "2026-10-09" } ], "pending_reboot": false },
  "software": { "status": "ok", "error": null, "installed": [ { "name": "Google Chrome", "version": "131.0.6778.86", "publisher": "Google LLC" }, { "name": "Adobe Acrobat Reader", "version": "24.4.20220", "publisher": "Adobe" }, { "name": "7-Zip", "version": "24.08", "publisher": "Igor Pavlov" } ] },
  "protection": {
    "bitlocker": { "status": "ok", "error": null, "os_volume_protection": "on", "os_volume_encryption_pct": 100, "encryption_method": "XtsAes128" },
    "defender": { "status": "ok", "error": null, "antivirus_enabled": true, "realtime_enabled": true, "tamper_protected": true, "signature_age_days": 0, "third_party_av": null },
    "cfa": { "status": "ok", "error": null, "mode": "enabled" },
    "asr": { "status": "ok", "error": null, "rules": [ { "id": "d4f940ab-401b-4efc-aadc-ad5f3c50688a", "action": "block" }, { "id": "c1db55ab-c21a-4637-bb3f-a12568109d35", "action": "block" }, { "id": "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550", "action": "block" } ] }
  },
  "recovery": { "status": "ok", "error": null, "winre_enabled": true, "system_restore_enabled": true, "restore_point_count": 2, "latest_restore_point": "2026-11-10T09:12:00Z" }
}
```

**Fixture 2 — `scan.no-bitlocker.json`** (expected: Protections red; others green). Differs from Fixture 1 only in `run_id` and `protection.bitlocker`:

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-11-14T16-50-11Z_0002",
  "collected_at": "2026-11-14T16:50:11Z",
  "collector_version": "0.1.0",
  "duration_ms": 9105,
  "host": { "hostname_hash": "sha256:2222", "os_caption": "Microsoft Windows 11 Pro", "os_build": "22631", "os_edition": "Professional", "is_admin": true, "ps_version": "5.1.22621.4391" },
  "backup": { "status": "ok", "error": null, "file_history_enabled": true, "file_history_last_backup": "2026-11-13T22:00:00Z", "windows_backup_last_success": null, "onedrive_kfm_folders": ["Desktop", "Documents", "Pictures"], "shadow_copy_count": 3, "third_party_agents": [] },
  "patch": { "status": "ok", "error": null, "hotfix_count": 14, "latest_hotfix_installed_on": "2026-11-05", "days_since_latest_hotfix": 9, "hotfixes": [ { "kb": "KB5044285", "installed_on": "2026-11-05" } ], "pending_reboot": false },
  "software": { "status": "ok", "error": null, "installed": [ { "name": "Google Chrome", "version": "131.0.6778.86", "publisher": "Google LLC" } ] },
  "protection": {
    "bitlocker": { "status": "ok", "error": null, "os_volume_protection": "off", "os_volume_encryption_pct": 0, "encryption_method": null },
    "defender": { "status": "ok", "error": null, "antivirus_enabled": true, "realtime_enabled": true, "tamper_protected": true, "signature_age_days": 0, "third_party_av": null },
    "cfa": { "status": "ok", "error": null, "mode": "enabled" },
    "asr": { "status": "ok", "error": null, "rules": [ { "id": "d4f940ab-401b-4efc-aadc-ad5f3c50688a", "action": "block" } ] }
  },
  "recovery": { "status": "ok", "error": null, "winre_enabled": true, "system_restore_enabled": true, "restore_point_count": 2, "latest_restore_point": "2026-11-10T09:12:00Z" }
}
```

> Variant to also keep: `scan.home-edition.json` — `os_edition: "Core"`, `bitlocker.status: "unavailable"`, `error: "BitLocker management not available on Windows Home"`. Expected: Protections **amber** with "consider Device Encryption / upgrade to Pro" explanation, not red.

**Fixture 3 — `scan.defender-off.json`** (expected: Protections red; Patch amber; overall red). Non-admin run, so admin-only fields are `unavailable`/`null`:

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-11-14T17-02-44Z_0003",
  "collected_at": "2026-11-14T17:02:44Z",
  "collector_version": "0.1.0",
  "duration_ms": 6230,
  "host": { "hostname_hash": "sha256:3333", "os_caption": "Microsoft Windows 10 Pro", "os_build": "19045", "os_edition": "Professional", "is_admin": false, "ps_version": "5.1.19041.5007" },
  "backup": { "status": "ok", "error": null, "file_history_enabled": false, "file_history_last_backup": null, "windows_backup_last_success": null, "onedrive_kfm_folders": ["Documents"], "shadow_copy_count": null, "third_party_agents": [] },
  "patch": { "status": "ok", "error": null, "hotfix_count": 9, "latest_hotfix_installed_on": "2026-09-20", "days_since_latest_hotfix": 55, "hotfixes": [ { "kb": "KB5043064", "installed_on": "2026-09-20" } ], "pending_reboot": true },
  "software": { "status": "ok", "error": null, "installed": [ { "name": "Google Chrome", "version": "118.0.5993.118", "publisher": "Google LLC" } ] },
  "protection": {
    "bitlocker": { "status": "unavailable", "error": "Requires administrator rights", "os_volume_protection": null, "os_volume_encryption_pct": null, "encryption_method": null },
    "defender": { "status": "ok", "error": null, "antivirus_enabled": false, "realtime_enabled": false, "tamper_protected": false, "signature_age_days": 21, "third_party_av": null },
    "cfa": { "status": "ok", "error": null, "mode": "disabled" },
    "asr": { "status": "ok", "error": null, "rules": [] }
  },
  "recovery": { "status": "ok", "error": null, "winre_enabled": null, "system_restore_enabled": true, "restore_point_count": null, "latest_restore_point": null }
}
```

### 0.8 Output contract: engine → UI/PDF

- **File:** `report.json` in the same run folder, beside `report.html` and `action-plan.pdf`.
- **Schema:** `/shared/contract/report.schema.json`. Frank builds the UI against `/shared/fixtures/report.*.json` (generated once by Tshedi from the §0.7 fixtures, committed, and regenerated on every engine rule change).

```jsonc
{
  "schema_version": "1.0.0",
  "run_id": "2026-11-14T17-02-44Z_0003",   // copied from scan.json
  "generated_at": "2026-11-14T17:02:46Z",
  "engine_version": "0.1.0",
  "baseline_version": "2026-11-01",         // from software-baseline.json
  "overall": "red",                          // red | amber | green — worst of rated categories
  "summary": "2 urgent issues need attention this week.", // one plain-English line for the header
  "categories": [                            // ALWAYS exactly 5, in this fixed order:
                                             // backup, patch, software, protection, recovery
    {
      "id": "protection",
      "title": "Ransomware protections",
      "status": "red",                       // red | amber | green | unavailable | failed
      "explanation": "Microsoft Defender antivirus is switched off, so nothing is scanning for ransomware.",
      "evidence": [                          // 1..8 rows, shown as a two-column table
        { "label": "Defender antivirus", "value": "Off", "status": "red" },
        { "label": "Controlled Folder Access", "value": "Disabled", "status": "amber" },
        { "label": "BitLocker (C:)", "value": "Not checked — needs admin", "status": "unavailable" }
      ],
      "fix_ids": ["enable-defender", "enable-cfa"] // keys into `fixes`
    }
  ],
  "fixes": [                                 // every fix referenced by any category
    {
      "id": "enable-defender",
      "category": "protection",
      "severity": "red",                     // red | amber
      "title": "Turn Microsoft Defender back on",
      "why": "Without antivirus, ransomware can run unnoticed.",
      "steps": ["Open Start → Windows Security", "Virus & threat protection → Manage settings", "Switch Real-time protection On"],
      "effort_minutes": 5,
      "needs_admin": true
    }
  ],
  "top_fixes": ["enable-defender", "install-updates", "turn-on-file-history"], // exactly ≤3 ids, ranked
  "scan": { "is_admin": false, "duration_ms": 6230, "os_caption": "Microsoft Windows 10 Pro" }
}
```

| Field | Type | Meaning / rule |
|---|---|---|
| `overall` | enum | Worst of categories with status red/amber/green. If all 5 are `unavailable`/`failed`, `overall` = `amber`. |
| `categories` | array[5] | Fixed order; UI never sorts. |
| `categories[].status` | enum | See §0.9. |
| `categories[].explanation` | string ≤ 200 chars | Plain English, Grade 8 reading level, no jargon without a gloss. |
| `categories[].evidence[]` | `{label, value, status}` | Facts from `scan.json`, human-formatted (dates as "13 Nov 2026"). |
| `fixes[]` | object | Single source for UI cards and PDF. `steps` 1–5 items. |
| `top_fixes` | string[] ≤3 | **Ranking rule:** red before amber → category order (protection, backup, patch, recovery, software) → lower `effort_minutes`. Empty only if all green. |

The PDF (one page) renders: header (`overall`, `summary`, date), the 5 category statuses as a strip, then the `top_fixes` with `title`, `why`, `steps`. Nothing else. HTML renders everything.

### 0.9 "unavailable" vs "failed"

| Status | Who sets it | Means | Example | UI shows | Counts toward `overall`? |
|---|---|---|---|---|---|
| `unavailable` | Collector (expected limitation) | We **knew** we couldn't check | Not admin; BitLocker on Home edition; Defender passive because 3rd-party AV | Grey badge "Not checked" + reason + "Run as administrator for a full check" | No |
| `failed` | Collector or engine (unexpected) | We **tried** and it broke | Cmdlet threw; timeout; malformed input | Grey-striped badge "Check failed" + short error | No, but `summary` mentions it |
| red/amber/green | Engine only | Rated result | — | Coloured badge | Yes |

Rules:
1. Collector wraps every probe in `try/catch`; a catch → `failed`, a precondition miss → `unavailable`. Never both.
2. A category is `unavailable`/`failed` only if **all** its probes are; otherwise it is rated on what was collected and the missing probes appear as evidence rows with that status.
3. The engine never converts `unavailable` into red. Lack of evidence is not evidence of risk — except **backup**, where "no backup evidence found" with `status: ok` is red (absence is the finding).

### 0.10 Contract change procedure

1. Open a PR on branch `contract/<change>` touching only `/shared/contract` and `/shared/fixtures`.
2. Bump `schema_version` (minor for added optional fields, major for anything else).
3. **Contract sign-off and freeze: 16:00 Day 1** (end of challenge planning, §8.4). Before sign-off, changes need Shakir (contract owner) and Tshedi (lead).
4. **After 16:00, any change needs all four members to agree in the team channel** — four explicit "agree" replies — before the PR is opened (Manual maintenance note).
5. The PR updates §0, Appendix A, `shared/contract/CHANGELOG.md` and the fixtures together.
6. After merge, each owner rebases and re-runs their isolation test (§0.2).

---

## §1 Environment & prerequisites

> Do all of §1 **at home, on home Wi-Fi, before travelling.** Target: every machine can run `npm ci`, `pip install`, and `npm run dist` with the network cable unplugged.

### 1.1 Version matrix

These pins are a known-compatible set. **Do not upgrade anything during the hackathon.** Lockfiles (`package-lock.json`, `requirements.txt` with `==`) are the real pins; this table is the human summary. On prep night, run each `--version` check and confirm the major matches.

| Tool | Pinned version | Why this version | Check |
|---|---|---|---|
| Windows | 10 22H2 (19045) or 11 23H2/24H2 | Target OS for collector; needs PowerShell 5.1 + Defender cmdlets | `winver` |
| Git for Windows | 2.47.x | Stable; includes Git Bash and credential manager | `git --version` |
| Node.js | 22 LTS (22.12.0+) | LTS through 2027; supported by Electron 34 toolchain and Vite 6 | `node -v` |
| npm | 10.9.x (ships with Node 22) | See §1.3 | `npm -v` |
| Python | 3.12.8 (64-bit) | Mature PyInstaller support; avoid 3.13 edge cases | `py -3.12 --version` |
| pip | 24.3.1 | Reliable `--no-index --find-links` offline installs | `python -m pip --version` |
| PowerShell | 5.1 (in-box) | The version every SMME machine has; **do not** use pwsh 7 for collector testing | `$PSVersionTable.PSVersion` |
| PyInstaller | 6.11.1 | Python 3.12 support, one-folder mode | in venv: `pyinstaller --version` |
| Electron | 34.0.0 | Chromium 132, Node 20.18 internally | `npx electron --version` |
| electron-builder | 25.1.8 | NSIS target, works with Electron 34 | `npx electron-builder --version` |
| electron-vite | 3.0.0 | Single Vite config for main/preload/renderer; supports Vite 6 | — |
| Vite | 6.0.7 | Required by `@tailwindcss/vite` 4 | `npx vite --version` |
| Tailwind CSS | 4.0.0 | v4 CSS-first config, Vite plugin | — |
| shadcn CLI | 2.3.0 | Supports Tailwind v4 + React 19 init | `npx shadcn@2.3.0 --version` |
| VS Code | latest stable on prep night | Editor | `code --version` |

### 1.2 Install steps (per machine)

Every team member does steps 1–12. Run in an **elevated PowerShell** unless stated.

1. Install `winget` updates: open Microsoft Store → Library → Update "App Installer".
2. Install Git:
   ```powershell
   # cwd: any
   winget install --id Git.Git -e --version 2.47.1
   ```
3. Configure Git identity and line endings:
   ```powershell
   # cwd: any
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   git config --global core.autocrlf true
   git config --global pull.rebase true
   ```
4. Install Node.js 22 LTS:
   ```powershell
   # cwd: any
   winget install --id OpenJS.NodeJS.LTS -e
   ```
   Close and reopen the terminal, then run `node -v` — must print `v22.x`.
5. Install Python 3.12 (tick "Add to PATH" is handled by the flag):
   ```powershell
   # cwd: any
   winget install --id Python.Python.3.12 -e
   ```
6. Upgrade pip globally (venvs get their own in §1.8):
   ```powershell
   # cwd: any
   py -3.12 -m pip install --upgrade pip==24.3.1
   ```
7. Confirm PowerShell 5.1 is present:
   ```powershell
   # cwd: any
   powershell.exe -NoProfile -Command '$PSVersionTable.PSVersion'
   ```
8. Set your user execution policy (see §1.4):
   ```powershell
   # cwd: any
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```
9. Install VS Code:
   ```powershell
   # cwd: any
   winget install --id Microsoft.VisualStudioCode -e
   ```
10. Install VS Code extensions:
    ```powershell
    # cwd: any
    code --install-extension ms-python.python
    code --install-extension ms-python.vscode-pylance
    code --install-extension charliermarsh.ruff
    code --install-extension ms-vscode.powershell
    code --install-extension dbaeumer.vscode-eslint
    code --install-extension esbenp.prettier-vscode
    code --install-extension bradlc.vscode-tailwindcss
    code --install-extension redhat.vscode-yaml
    code --install-extension eamodio.gitlens
    ```
11. Clone the repo:
    ```powershell
    # cwd: C:\dev
    git clone https://github.com/<org>/antigravity.git
    ```
12. Run the full offline prep in §1.5 and tick every box.

**Only Schwan (D), additionally:**

13. Install Hyper-V (Windows Pro) and create a clean Windows 11 VM snapshot named `clean-baseline` for installer tests. Download the Windows 11 dev/eval VHD **at home** (it is ~20 GB).

**Tailwind v4 + shadcn/ui init (done once by Frank, then committed — others just `npm ci`):**

14. ```powershell
    # cwd: antigravity/desktop
    npm install -D tailwindcss@4.0.0 @tailwindcss/vite@4.0.0
    ```
15. Create `desktop/src/renderer/src/styles/globals.css` containing `@import "tailwindcss";` and add `tailwindcss()` to the renderer plugins in `electron.vite.config.ts`.
16. ```powershell
    # cwd: antigravity/desktop
    npx shadcn@2.3.0 init
    ```
    Choose: style **New York**, base colour **Neutral**, CSS variables **yes**.
17. Add the components we use:
    ```powershell
    # cwd: antigravity/desktop
    npx shadcn@2.3.0 add button card badge input progress table alert separator
    ```
18. Repeat steps 14–16 in `antigravity/landing` (components: `button card badge`).
19. Commit `components.json` and `src/components/ui/*` — shadcn components are copied source, so the venue needs no network for them.

### 1.3 Package manager decision: npm

**Default: npm 10 (bundled with Node 22).** Rationale: electron-builder resolves native/production dependencies by walking `node_modules`, and pnpm's symlinked layout needs `node-linker=hoisted` workarounds — one less thing to break at 03:00. npm also needs zero extra install.

Rules:
- Always `npm ci` (not `npm install`) after pulling — it uses the lockfile exactly.
- Only the sub-project owner adds dependencies, and commits `package-lock.json` in the same commit.
- No npm workspaces — each JS sub-project is installed separately (§1.8). Reason: keeps `/desktop` packaging self-contained for electron-builder.

### 1.4 PowerShell 5.1 and execution policy

| Context | How the collector runs | Why |
|---|---|---|
| Developer testing | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\collector.ps1 -OutputPath .\out\scan.json` | `Bypass` applies to that one process only; does not change machine policy |
| Inside the app | Electron main spawns the same command line with absolute path to the bundled script | SMME machines often have `Restricted` policy; per-process bypass is the standard, non-persistent approach |
| Your dev machine | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` | Lets you run local scripts while still blocking unsigned downloaded ones |

Rules:
1. **Never** call `Set-ExecutionPolicy` from the collector or app — it is a write, and the agent is read-only.
2. Always launch `powershell.exe` (5.1), never `pwsh.exe` (7). `Get-MpComputerStatus` and `Get-BitLockerVolume` modules behave differently under 7.
3. Test the collector twice: normal PowerShell and "Run as administrator" — both must produce valid `scan.json` (§0.9).
4. Save `.ps1` files as **UTF-8 with BOM**; PowerShell 5.1 misreads non-ASCII characters in BOM-less files. Add to `.editorconfig` (tree in Appendix C).

### 1.5 Download-everything-before-you-travel checklist

Each member ticks their own sheet; Shakir collects screenshots of the final "offline test" in the team chat by **the night before Day 1**. Deadlines (T−5 to T−1) and per-member time estimates: §8.3.

**All members**
- [ ] Repo cloned, `main` pulled on prep night.
- [ ] In `/desktop`: `npm ci` completed (populates `%LOCALAPPDATA%\npm-cache`).
- [ ] In `/landing`: `npm ci` completed.
- [ ] In `/engine`: venv created and `pip install -r requirements.txt` completed (§1.8).
- [ ] Python wheelhouse downloaded:
  ```powershell
  # cwd: antigravity/engine
  py -3.12 -m pip download -r requirements.txt -r requirements-dev.txt -d ..\.offline\wheelhouse
  ```
- [ ] Electron binary cached (§1.6) — `npx electron --version` works with Wi-Fi **off**.
- [ ] electron-builder caches warmed: run `npm run dist` once in `/desktop` (downloads NSIS and winCodeSign).
- [ ] **Offline test:** turn Wi-Fi off, delete `desktop\node_modules`, run `npm ci --prefer-offline --no-audit --fund=false`, then `npm run dev`. App window opens → ✅.
- [ ] Offline docs: save PDFs/HTML of Electron IPC docs, PyInstaller "spec files" page, Tailwind v4 docs, shadcn component pages, and Microsoft docs for `Get-MpComputerStatus`, `Get-MpPreference`, `Get-BitLockerVolume`, `Get-HotFix` into `antigravity/.offline/docs/` (git-ignored).
- [ ] Security test tools downloaded into `antigravity/.offline/tools/`: Process Monitor, Strings, Sigcheck (Sysinternals) and 7-Zip (§7.2).
- [ ] Phone hotspot data bundle bought (≥ 2 GB) as last resort.

**Extra for Schwan (D)**
- [ ] Start the Windows 11 VM download at **T−5** (§8.3) — it is the longest download.
- [ ] USB stick (≥ 32 GB) containing: `.offline/` folder copied from his machine, `%LOCALAPPDATA%\electron\Cache`, `%LOCALAPPDATA%\electron-builder\Cache`, Node 22 MSI, Python 3.12 installer, Git installer, VS Code installer. This is the team's recovery kit.
- [ ] Clean VM snapshot created and tested.

**Extra for Tshedi (A)**
- [ ] PyInstaller build run once at home: `pyinstaller engine.spec` succeeds, `dist\engine\engine.exe --help` runs.
- [ ] Baseline JSON first draft committed with real current versions (looked up at home — no live lookups in product).

### 1.6 Electron offline: ELECTRON_MIRROR and caches

Electron's npm package downloads a ~100 MB zip from GitHub in its `postinstall` — the #1 venue-Wi-Fi failure. electron-builder then downloads NSIS and winCodeSign on first `dist`.

| Cache | Default location | Env var to override |
|---|---|---|
| Electron binary zip | `%LOCALAPPDATA%\electron\Cache` | `electron_config_cache` |
| electron-builder tools (NSIS, winCodeSign) | `%LOCALAPPDATA%\electron-builder\Cache` | `ELECTRON_BUILDER_CACHE` |
| npm packages | `%LOCALAPPDATA%\npm-cache` | `npm_config_cache` |

Steps:

1. Warm the Electron cache at home:
   ```powershell
   # cwd: antigravity/desktop
   npm ci
   dir $env:LOCALAPPDATA\electron\Cache
   ```
   You must see `electron-v34.0.0-win32-x64.zip`. If missing, run `node node_modules\electron\install.js`.
2. Warm electron-builder:
   ```powershell
   # cwd: antigravity/desktop
   npm run dist
   ```
3. If Electron download fails at home (GitHub throttling), use a mirror for that one install:
   ```powershell
   # cwd: antigravity/desktop
   $env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
   npm ci
   Remove-Item Env:ELECTRON_MIRROR
   ```
4. **At the venue, on a machine whose cache is empty**, restore from Schwan's USB:
   ```powershell
   # cwd: any
   robocopy E:\kit\electron-cache $env:LOCALAPPDATA\electron\Cache /E
   robocopy E:\kit\electron-builder-cache $env:LOCALAPPDATA\electron-builder\Cache /E
   ```
5. Last resort — install with the binary download skipped and point at a local unzipped copy:
   ```powershell
   # cwd: antigravity/desktop
   $env:ELECTRON_SKIP_BINARY_DOWNLOAD = "1"
   npm ci --prefer-offline
   Expand-Archive E:\kit\electron-cache\electron-v34.0.0-win32-x64.zip node_modules\electron\dist
   Set-Content node_modules\electron\path.txt "electron.exe" -NoNewline
   ```
6. Add to `/desktop/.npmrc` (committed) so installs prefer the cache by default:
   ```
   prefer-offline=true
   audit=false
   fund=false
   ```

### 1.7 Monorepo folder tree

The complete annotated tree — every folder and file referenced anywhere in this manual, with owner letters — is **Appendix C**. Top-level layout:

```
antigravity/
├── shared/       the contract: schemas, fixtures, licence public key (§0, Appendix A)
├── engine/       Brick A — Python scoring engine (§2)
├── baseline/     Brick A — curated software baseline (§2.8)
├── collector/    Brick B — PowerShell 5.1 read-only collector (§3)
├── desktop/      Bricks C (renderer), B (licence), D (main process, build) (§4, §5)
├── landing/      Brick C — Vite landing page on Vercel (§4.13)
├── installer/    Brick D — build, checksum, smoke-test and NSIS scripts (§5)
├── tools/        dev-only: licence issuing, security test scripts (§3.11, §7.2)
├── fallback/     demo fallback artefacts, git-ignored (§9.6)
└── docs/         this manual, decisions log, security results, demo script
```

### 1.8 Environments and isolation

| Environment | Location | Created by | Isolated how |
|---|---|---|---|
| Engine Python venv | `engine/.venv/` | Each member who runs the engine | Own interpreter + site-packages; never `pip install` outside it |
| Desktop node_modules | `desktop/node_modules/` | `npm ci` in `/desktop` | Own lockfile; no workspaces |
| Landing node_modules | `landing/node_modules/` | `npm ci` in `/landing` | Own lockfile; never bundled into installer |
| Collector | none | — | PowerShell 5.1 in-box; zero external modules allowed |

Create the engine venv:

1. ```powershell
   # cwd: antigravity/engine
   py -3.12 -m venv .venv
   ```
2. ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -m pip install --upgrade pip==24.3.1
   ```
3. Online install:
   ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
   ```
   Offline install (venue):
   ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -m pip install --no-index --find-links ..\.offline\wheelhouse -r requirements.txt -r requirements-dev.txt
   ```
4. In VS Code: `Ctrl+Shift+P` → "Python: Select Interpreter" → `engine\.venv\Scripts\python.exe`.

Rule: always call `.venv\Scripts\python` explicitly in scripts and docs — never rely on an "activated" shell.

### 1.9 Git workflow

**Branches**

| Branch | Owner | Purpose |
|---|---|---|
| `main` | Tshedi (merges) | Always builds; demo is cut from here |
| `brick/engine` | Tshedi | Brick A |
| `brick/collector` | Shakir | Brick B |
| `brick/desktop-ui` | Frank | Brick C renderer |
| `brick/landing` | Frank | Landing page |
| `brick/packaging` | Schwan | Brick D |
| `contract/<topic>` | Shakir | Contract changes only; after 16:00 Day 1 needs all four members (§0.10) |
| `fix/<short-name>` | anyone | Post-integration fixes |

**Commit convention** (Conventional Commits, scope = brick):
```
feat(collector): add CFA and ASR probes
fix(engine): treat home edition BitLocker as amber
chore(installer): bump NSIS include
contract: add backup.third_party_agents (1.1.0)
```

**PR / merge rules**
1. Rebase your brick branch on `main` before opening a PR: `git pull --rebase origin main`.
2. PR description includes the isolation-test output (§0.2) pasted in.
3. One approval from any other member; **contract PRs after 16:00 Day 1 need all four members to agree in the team channel first** (§0.10).
4. Tshedi merges (squash merge). If Tshedi is unavailable for > 30 min or asleep (02:00–04:00, §8.5), Shakir merges.
5. Merge to `main` at least every 3 hours during hacking — small merges beat a 06:00 big-bang.
6. **No force-push to any shared branch after 19:00 Day 1.** If history is wrong, add a revert commit.
7. Tag milestones: `pre-integration`, `merged-bricks`, `v0.1-integrated`, `v0.2-installer`, `v1.0.0-rc1`, `v1.0.0-rc2` (optional), `v1.0.0-demo` — times below and in §8.7.

**Timeline anchors** (programme times as quoted in the brief; full plan in §8)

| Time | Git event |
|---|---|
| Day 1 16:00 | Contract signed off and frozen (§0.10); hacking starts — everyone branches from `main` |
| Day 1 19:00 | Force-push ban begins; integration starts — tags `pre-integration`, then `merged-bricks` (§6.2) |
| Day 1 21:00 | Target: `v0.1-integrated` (end-to-end dev-mode scan, §6.6) |
| Day 1 ~00:00 | Target: `v0.2-installer` (first installer on a clean-ish machine, §6.7) |
| Day 2 06:00 | Feature freeze — only `fix/*` branches labelled `security-critical` or `demo-blocking` |
| Day 2 06:45 | Build and tag `v1.0.0-rc1` (§8.7) |
| Day 2 10:30–11:00 | Final hacking — critical fixes only; `v1.0.0-rc2` at 10:55 only if a fix merged |
| Day 2 11:00–11:15 | Mentor checkpoint — demo RC1 on the demo laptop |
| Day 2 11:20 | Tag `v1.0.0-demo` on the submitted RC; GitHub Release by 11:25 |
| Day 2 11:30 | **Submit** (hard deadline ~11:45; buffer non-negotiable) |

### 1.10 Dependency manifests

#### `/desktop/package.json`

```json
{
  "name": "antigravity-desktop",
  "version": "0.1.0",
  "private": true,
  "main": "out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "test": "vitest run",
    "dist": "electron-vite build && electron-builder --win nsis"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "3.0.1",
    "lucide-react": "0.471.0",
    "@radix-ui/react-slot": "1.1.1",
    "@radix-ui/react-progress": "1.1.1",
    "@radix-ui/react-separator": "1.1.1",
    "zod": "3.24.1"
  },
  "devDependencies": {
    "electron": "34.0.0",
    "electron-builder": "25.1.8",
    "electron-vite": "3.0.0",
    "vite": "6.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "typescript": "5.7.3",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "@types/node": "22.10.7",
    "tailwindcss": "4.0.0",
    "@tailwindcss/vite": "4.0.0",
    "tw-animate-css": "1.2.0",
    "vitest": "2.1.8",
    "@testing-library/react": "16.1.0",
    "jsdom": "25.0.1"
  }
}
```

| Package | Version | Tag | Reason |
|---|---|---|---|
| react / react-dom | 19.0.0 | MVP | UI framework; shadcn's current target |
| class-variance-authority | 0.7.1 | MVP | shadcn component variants |
| clsx | 2.1.1 | MVP | Conditional class names for `cn()` |
| tailwind-merge | 3.0.1 | MVP | Tailwind v4-aware class merging for `cn()` |
| lucide-react | 0.471.0 | MVP | Status icons (shield, check, alert) |
| @radix-ui/react-slot / progress / separator | 1.1.1 | MVP | Primitives behind shadcn Button, Progress, Separator |
| zod | 3.24.1 | MVP | Validate `report.json` at runtime before rendering |
| electron | 34.0.0 | MVP | Desktop shell (cached, §1.6) |
| electron-builder | 25.1.8 | MVP | NSIS Windows installer |
| electron-vite | 3.0.0 | MVP | One config for main/preload/renderer with HMR |
| vite | 6.0.7 | MVP | Bundler; required by Tailwind v4 plugin |
| @vitejs/plugin-react | 4.3.4 | MVP | JSX + fast refresh |
| typescript | 5.7.3 | MVP | Type-checks against `shared/contract/types.ts` |
| @types/react, @types/react-dom, @types/node | 19.0.7 / 19.0.3 / 22.10.7 | MVP | Typings |
| tailwindcss + @tailwindcss/vite | 4.0.0 | MVP | Styling, v4 CSS-first config |
| tw-animate-css | 1.2.0 | MVP | Animation utilities shadcn expects on v4 |
| vitest | 2.1.8 | MVP | Renderer isolation test (§0.2) |
| @testing-library/react | 16.1.0 | MVP | Render components in tests |
| jsdom | 25.0.1 | MVP | DOM for vitest |

No license library: **Default:** Ed25519 verification via Node's built-in `node:crypto` — zero dependencies, works offline.

#### `/landing/package.json`

```json
{
  "name": "antigravity-landing",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "3.0.1",
    "lucide-react": "0.471.0",
    "@radix-ui/react-slot": "1.1.1"
  },
  "devDependencies": {
    "vite": "6.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "typescript": "5.7.3",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "tailwindcss": "4.0.0",
    "@tailwindcss/vite": "4.0.0",
    "tw-animate-css": "1.2.0"
  }
}
```

| Package | Version | Tag | Reason |
|---|---|---|---|
| react / react-dom | 19.0.0 | MVP | Same as desktop — shared knowledge, shared components |
| cva, clsx, tailwind-merge, @radix-ui/react-slot | as desktop | MVP | shadcn Button/Card/Badge |
| lucide-react | 0.471.0 | MVP | Icons matching the app |
| vite + @vitejs/plugin-react | 6.0.7 / 4.3.4 | MVP | Build for Vercel static hosting |
| typescript + @types | 5.7.3 | MVP | Type safety |
| tailwindcss + @tailwindcss/vite + tw-animate-css | 4.0.0 / 4.0.0 / 1.2.0 | MVP | Same styling stack as desktop |

**Default:** deploy landing via Vercel Git integration on `main` **the night before**, so the venue only needs a `git push`; if Wi-Fi is down, the already-deployed version is the submission.

#### `/engine/requirements.txt` (runtime — bundled by PyInstaller)

```
pydantic==2.10.5
jsonschema==4.23.0
Jinja2==3.1.5
reportlab==4.2.5
packaging==24.2
```

| Package | Version | Tag | Reason |
|---|---|---|---|
| pydantic | 2.10.5 | MVP | Typed models for `scan.json`/`report.json`; clear errors on bad input |
| jsonschema | 4.23.0 | MVP | Validate against the *same* `/shared/contract/*.schema.json` the TS side uses |
| Jinja2 | 3.1.5 | MVP | HTML report templating |
| reportlab | 4.2.5 | MVP | One-page PDF; pure Python wheels — no GTK, unlike WeasyPrint |
| packaging | 24.2 | MVP | Correct version comparison for the software baseline (`131.0 > 118.0`) |

#### `/engine/requirements-dev.txt` (not bundled)

```
pytest==8.3.4
pyinstaller==6.11.1
ruff==0.8.6
```

| Package | Version | Tag | Reason |
|---|---|---|---|
| pytest | 8.3.4 | MVP | Engine isolation test (§0.2) |
| pyinstaller | 6.11.1 | MVP | Builds `engine.exe` (one-folder mode for fast start-up) |
| ruff | 0.8.6 | MVP | Lint + format in one fast tool |

#### `/collector` — no dependencies

PowerShell 5.1 in-box cmdlets only (`Get-HotFix`, `Get-ItemProperty`, `Get-MpComputerStatus`, `Get-MpPreference`, `Get-BitLockerVolume`, `Get-ComputerRestorePoint`, `Get-CimInstance`). **No PSGallery modules** — SMME machines won't have them and installing is a write.

---

## §2 Brick A: Assessment Engine (Tshedi)

The engine reads one `scan.json` (§0.5), applies the rules in this section, and writes `report.json` (§0.8), `report.html` and `action-plan.pdf`. It is pure and deterministic: same input + same baseline → same output. It never touches the network or the Windows machine.

### 2.1 Folder layout

This refines the `/engine` part of the §1.7 tree. New files are marked ✚.

```
engine/
├── .venv/                          (git-ignored) §2.2
├── requirements.txt                runtime pins (§1.10)
├── requirements-dev.txt            test/build pins (§1.10)
├── engine.spec                     PyInstaller spec (§2.12)
├── tools/
│   └── validate.py             ✚   schema gate: validate.py scan|report <file> (§6.3)
├── antigravity_engine/
│   ├── __init__.py                 __version__ = "0.1.0"
│   ├── __main__.py                 CLI entry (§2.11)
│   ├── contract.py                 pydantic models for scan.json / report.json
│   ├── parser.py               ✚   load + validate scan.json → ScanModel
│   ├── baseline.py             ✚   load + validate software-baseline.json
│   ├── clock.py                ✚   "now" = scan.collected_at; date helpers
│   ├── paths.py                ✚   resource() for frozen vs dev (§2.12)
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── result.py           ✚   CategoryResult, EvidenceRow dataclasses
│   │   ├── backup.py               §2.5.1
│   │   ├── patch.py                §2.5.2
│   │   ├── software.py             §2.5.3
│   │   ├── protection.py           §2.5.4
│   │   ├── recovery.py             §2.5.5
│   │   └── fixes.py                fix catalogue (§2.9) + top-3 ranking
│   ├── aggregator.py           ✚   5 results → overall RAG (§2.6)
│   ├── risk.py                 ✚   weighted risk score → summary sentence (§2.6)
│   ├── report_model.py         ✚   builds ReportModel, validates vs report.schema.json
│   ├── render/
│   │   ├── html.py                 Jinja2 → report.html
│   │   └── pdf.py                  ReportLab → action-plan.pdf
│   └── templates/
│       └── report.html.j2
└── tests/
    ├── conftest.py             ✚   fixture loaders + make_scan() helper
    ├── test_backup.py          ✚
    ├── test_patch.py           ✚
    ├── test_software.py        ✚
    ├── test_protection.py      ✚
    ├── test_recovery.py        ✚
    ├── test_ranking.py
    ├── test_fixtures.py            end-to-end over /shared/fixtures
    ├── test_cli.py             ✚   exit codes, bad input
    ├── test_render.py          ✚   PDF exactly one page; HTML autoescape (§4.10–§4.11)
    └── test_integrity.py       ✚   report invariants RPT-01..03, 06 (§7.6)
baseline/
├── software-baseline.json          §2.8
└── software-baseline.schema.json ✚ §2.8
```

### 2.2 Venv and dependencies

Follow §1.8 for the full procedure. Short form:

1. ```powershell
   # cwd: antigravity/engine
   py -3.12 -m venv .venv
   ```
2. ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -m pip install --no-index --find-links ..\.offline\wheelhouse -r requirements.txt -r requirements-dev.txt
   ```
   (Online at home: drop `--no-index --find-links …`.)
3. Confirm:
   ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -c "import pydantic, jsonschema, jinja2, reportlab, packaging; print('ok')"
   ```

`requirements.txt` — unchanged from §1.10 (reasons are in that table):

```
pydantic==2.10.5
jsonschema==4.23.0
Jinja2==3.1.5
reportlab==4.2.5
packaging==24.2
```

### 2.3 Module breakdown

Data flows top to bottom. Each module is unit-testable alone.

| # | Module | File | Responsibility | Inputs | Outputs |
|---|---|---|---|---|---|
| 1 | Input parser | `parser.py` | Read bytes, reject BOM/invalid JSON, validate against `scan.schema.json`, check major `schema_version`, build typed model | path to `scan.json` | `ScanModel` or `ContractError` |
| 2 | Clock | `clock.py` | Fix "now" to `collected_at`; `days_between()`, `parse_iso()` | `ScanModel.collected_at` | `datetime` helpers |
| 3 | Baseline loader | `baseline.py` | Load + validate baseline, pre-compile regexes | path to `software-baseline.json` | `Baseline` |
| 4 | Per-category scorers | `scoring/backup.py` … `recovery.py` | Apply §2.5 rules; one pure function `score(scan, ctx) -> CategoryResult` each | `ScanModel`, `Baseline` (software only), clock | `CategoryResult` (status, explanation, evidence, fix_ids) |
| 5 | Aggregator | `aggregator.py` | Fixed category order; compute `overall` per §0.8 | 5 × `CategoryResult` | `overall` RAG |
| 6 | Risk scorer | `risk.py` | Weighted score 0–100 (§2.6); pick `summary` sentence | 5 × `CategoryResult` | `risk_score` (internal), `summary` |
| 7 | Fix ranking | `scoring/fixes.py` | Resolve fix ids to catalogue entries; rank top 3 per §0.8 | all `fix_ids` | `fixes[]`, `top_fixes[]` |
| 8 | Report model builder | `report_model.py` | Assemble `report.json` dict; validate against `report.schema.json` before writing | outputs of 4–7 + scan metadata | `report.json` |
| 9 | Renderers | `render/html.py`, `render/pdf.py` | Render from the **report model only** — never from the scan | `ReportModel` | `report.html`, `action-plan.pdf` |

Rule: renderers read only `ReportModel`. That keeps the HTML, the PDF and Frank's UI showing identical facts.

### 2.4 How the engine consumes the contract

1. `parser.py` loads `/shared/contract/scan.schema.json`. In the frozen build it is bundled next to `engine.exe` (§2.12); in dev it is read from `../shared/contract/`.
2. Validation order:
   1. File exists and is ≤ 2 MB → else `ContractError("input missing or too large")`.
   2. No UTF-8 BOM, parses as JSON → else `ContractError("not valid JSON")`.
   3. `schema_version` major == `1` → else `ContractError("unsupported schema version")`.
   4. JSON Schema validation → else `ContractError(<first error path>)`.
3. Unknown extra keys are ignored (§0.6).
4. On `ContractError` the CLI still writes a `report.json` with all 5 categories `failed`, `overall: "amber"`, the error text in `summary`, and exits `2` (§2.11). The UI never has to handle "no report".
5. The engine **re-derives** values it can compute (e.g. days since latest hotfix from `latest_hotfix_installed_on` and `collected_at`) rather than trusting the collector's convenience fields. If they disagree by more than 1 day, the engine's value wins and an evidence note is added.

### 2.5 Scoring rules per category

Notation: a category's rules are evaluated top to bottom; **first match wins**. Each rule names the explanation text key and the fix id(s) it attaches (§2.9). "Days" are measured from `collected_at` (§2.3 clock).

#### 2.5.1 Backup evidence (`backup`)

"Backup evidence" = a dated, completed backup we can see. Sync (OneDrive) and snapshots (shadow copies) are **not** backups by themselves — ransomware encrypts synced files and deletes shadow copies.

| # | Condition | Status | Fix id |
|---|---|---|---|
| B1 | `backup.status` is `unavailable` / `failed` | same | — |
| B2 | Newest of `file_history_last_backup`, `windows_backup_last_success` is ≤ 7 days old | 🟢 green | — |
| B3 | Newest dated backup is 8–30 days old | 🟠 amber | `run-backup-now` |
| B4 | No dated backup, but `third_party_agents` non-empty | 🟠 amber | `verify-backup-agent` |
| B5 | No dated backup, but OneDrive KFM covers ≥ 1 folder **or** `shadow_copy_count` ≥ 1 | 🟠 amber | `turn-on-file-history` |
| B6 | Newest dated backup is > 30 days old | 🔴 red | `turn-on-file-history` |
| B7 | No evidence of any kind | 🔴 red | `turn-on-file-history` |

Note: absence of evidence **is** the finding for backup (§0.9 rule 3). A `null` caused by non-admin (`shadow_copy_count`, `windows_backup_last_success`) is shown as an evidence row "Not checked — needs admin" and does not by itself make the category red if another dated backup exists.

#### 2.5.2 Patch status (`patch`)

The 30/60-day heuristic. `Get-HotFix` misses some update types, so we judge the **newest** installed update date only.

| # | Condition | Status | Fix id |
|---|---|---|---|
| P1 | `patch.status` is `unavailable` / `failed` | same | — |
| P2 | `hotfix_count == 0` or `latest_hotfix_installed_on` is null | 🔴 red | `install-updates` |
| P3 | Days since latest hotfix > 60 | 🔴 red | `install-updates` |
| P4 | Days since latest hotfix 31–60 | 🟠 amber | `install-updates` |
| P5 | ≤ 30 days but `pending_reboot == true` | 🟠 amber | `restart-to-finish-updates` |
| P6 | ≤ 30 days, no pending reboot | 🟢 green | — |

**OS support overlay** (applied after P1–P6, can only make the result worse):

| Condition | Effect | Fix id |
|---|---|---|
| `host.os_build` starts with `19` (Windows 10) | at least 🟠 amber, explanation adds "Windows 10 support ended on 14 Oct 2025 unless you've enrolled in Extended Security Updates." | `plan-windows-11` |
| Windows 11 build older than the oldest supported release in `baseline.os.min_supported_build` | at least 🟠 amber | `plan-windows-11` |

**Default:** keep the supported-build list in the baseline file (`os` block, §2.8), not in code, so it can be updated without rebuilding the engine.

#### 2.5.3 Outdated software (`software`)

Each installed app is matched against baseline entries (§2.8) by `name_regex` (and `publisher_regex` if present). Versions compare with `packaging.version.Version`; unparseable versions fall back to dotted-integer comparison, and if that fails the app is reported as "version not readable" (amber-neutral, no effect on status).

| # | Condition | Status | Fix id |
|---|---|---|---|
| S1 | `software.status` is `unavailable` / `failed` | same | — |
| S2 | Any matched app has `eol: true` | 🔴 red | `update-outdated-apps` |
| S3 | Any matched app with `severity: "high"` is below `min_safe_version` | 🔴 red | `update-outdated-apps` |
| S4 | Any matched app with `severity: "medium"` is below `min_safe_version` | 🟠 amber | `update-outdated-apps` |
| S5 | All matched apps at or above `min_safe_version` | 🟢 green | — |
| S6 | Zero installed apps matched any baseline entry | 🟢 green, explanation "None of your N apps are on our watch list" | — |
| S7 | `installed` list is empty with status `ok` | 🟠 amber, explanation "We couldn't read the installed-apps list" | — |

Software absent from the baseline is **not assessed** — never red, never amber. The evidence table shows the outdated apps first (max 6 rows), then one row "N other apps not on our watch list".

One fix (`update-outdated-apps`) is generated whose `steps` list the outdated app names, so software can't fill all three top-fix slots.

#### 2.5.4 Ransomware protections (`protection`)

Four sub-checks. Each sub-check produces its own evidence row with its own status; the category status is the **worst** rated sub-check. Sub-checks whose own `status` is `unavailable`/`failed` appear as grey rows and are skipped for rating.

**Defender (`protection.defender`)**

| Condition | Row status | Fix id |
|---|---|---|
| `antivirus_enabled == false` and `third_party_av` is null | 🔴 red | `enable-defender` |
| `antivirus_enabled == false` and `third_party_av` is set | 🟢 green (row reads "Protected by <third_party_av>") | — |
| `realtime_enabled == false` | 🔴 red | `enable-defender` |
| `signature_age_days` > 7 | 🔴 red | `update-defender-definitions` |
| `signature_age_days` 4–7 | 🟠 amber | `update-defender-definitions` |
| `tamper_protected == false` | 🟠 amber | `enable-tamper-protection` |
| otherwise | 🟢 green | — |

**BitLocker (`protection.bitlocker`)**

| Condition | Row status | Fix id |
|---|---|---|
| `status: unavailable` and `host.os_edition` starts with `Core` (Home) | 🟠 amber — **rated, not grey** (we know the answer: no BitLocker management on Home) | `encrypt-device-home` |
| `status: unavailable` for any other reason (e.g. not admin) | grey "Not checked — needs admin" | — |
| `os_volume_protection == "off"` | 🔴 red | `turn-on-bitlocker` |
| `os_volume_protection == "on"` and `os_volume_encryption_pct` < 100 | 🟠 amber | — (explanation: "still encrypting; leave the PC on") |
| `os_volume_protection == "on"` | 🟢 green | — |

**Controlled Folder Access (`protection.cfa`)**

| `mode` | Row status | Fix id |
|---|---|---|
| `enabled` | 🟢 green | — |
| `audit` | 🟠 amber | `enable-cfa` |
| `disabled` | 🟠 amber | `enable-cfa` |

CFA off is amber, not red: it is a strong extra layer but commonly off, and it can block legitimate apps — we don't want it outranking "no antivirus".

**ASR rules (`protection.asr`)**

Baseline `asr.recommended` lists the rule GUIDs we expect (default: 3–5 ransomware-relevant rules, chosen by Shakir and Tshedi on prep night from Microsoft's ASR reference). Count rules in `block` or `warn`.

| Recommended rules blocking | Row status | Fix id |
|---|---|---|
| all | 🟢 green | — |
| at least 1 | 🟠 amber | `enable-asr-rules` |
| none | 🟠 amber | `enable-asr-rules` |

ASR is amber-max for the same reason as CFA. If Defender is off, the ASR and CFA rows note "Only works when Microsoft Defender is your antivirus" and are excluded from rating.

#### 2.5.5 Recovery readiness (`recovery`)

Can this PC be brought back if Windows breaks?

| # | Condition | Status | Fix id |
|---|---|---|---|
| R1 | `recovery.status` is `unavailable` / `failed` | same | — |
| R2 | `winre_enabled == false` and (`system_restore_enabled == false` or `restore_point_count == 0`) | 🔴 red | `enable-winre`, `turn-on-system-restore` |
| R3 | `winre_enabled == false` | 🟠 amber | `enable-winre` |
| R4 | `system_restore_enabled == false` | 🟠 amber | `turn-on-system-restore` |
| R5 | `restore_point_count == 0`, or `latest_restore_point` > 30 days old | 🟠 amber | `create-restore-point` |
| R6 | All of the above fine | 🟢 green | — |
| R7 | `winre_enabled` and `restore_point_count` both `null` (non-admin) but `system_restore_enabled == true` | 🟢 green with grey rows for the unknown fields, explanation adds "Run as administrator for a full check" | — |

### 2.6 Aggregation, weighting and top-3

**Overall RAG** — exactly as §0.8: the worst of the rated categories; all unrated → amber.

**Risk score (internal)** — used only to pick the `summary` sentence. It is not in the §0.8 contract; exposing it is **[STRETCH]** via a minor contract bump (§0.10).

| Category | Weight | Why |
|---|---|---|
| protection | 30 | Prevents the incident |
| backup | 30 | Decides whether a ransomware hit is survivable |
| patch | 20 | Most common way in |
| recovery | 10 | Speeds recovery; backups matter more |
| software | 10 | Real risk, but our baseline is small |

`risk_score = 100 × Σ(weight × points) / Σ(weight of rated categories)`, where red = 1.0, amber = 0.5, green = 0. Unavailable/failed categories are removed from both numerator and denominator.

| risk_score | count of red | `summary` |
|---|---|---|
| any | ≥ 1 | "{n} urgent issue(s) need attention this week." |
| ≥ 25 | 0 | "No urgent issues, but {n} things to tighten up." |
| < 25 | 0 | "This PC is in good shape. Keep it that way." |
| — | — | If any category `failed`, append " Some checks couldn't run." |

**Top-3 fixes** — exactly the §0.8 ranking rule, implemented in `scoring/fixes.py`. Duplicate fix ids from different rules are merged (e.g. `enable-defender` from two Defender rows appears once).

### 2.7 Keeping "unavailable" separate from "failed"

| Source | Engine handling |
|---|---|
| Whole section `status: unavailable` from collector | Category `status: "unavailable"`, explanation from the collector `error` mapped to plain English (table in `scoring/result.py`). Exception: BitLocker on Home → rated amber (§2.5.4). |
| Whole section `status: failed` from collector | Category `status: "failed"`, explanation "This check couldn't run on this PC." + short error. |
| Individual `null` field inside an `ok` section | Grey evidence row only; category still rated on the remaining fields. |
| Exception inside a scorer (engine bug) | Caught per category in `__main__.py` → that category `failed` with `explanation: "Internal error while checking."`; other categories unaffected; exit code stays `0` but stderr logs the traceback. |
| `ContractError` (bad input) | All five `failed`, exit `2` (§2.4). |

Two rules make this enforceable in code:

1. `CategoryResult.status` is an `Enum` with five members; `unavailable` and `failed` can only be constructed through `CategoryResult.unavailable(reason)` / `.failed(reason)`, never from a RAG comparison.
2. `aggregator.py` filters with `status in RATED` (`red`, `amber`, `green`) — a single set used everywhere.

### 2.8 Baseline JSON schema

- **Data:** `/baseline/software-baseline.json`
- **Schema:** `/baseline/software-baseline.schema.json` (draft 2020-12), validated on load
- **Bundled:** shipped beside the app via electron-builder `extraResources`; the app passes its path with `--baseline`.

```jsonc
{
  "baseline_version": "2026-11-01",        // shown in report.json → baseline_version
  "checked_on": "2026-11-01",              // date versions were last researched (at home, never live)
  "os": {
    "min_supported_build": { "win11": "22631" }, // §2.5.2 overlay; update on prep night
    "win10_eos_date": "2025-10-14"
  },
  "asr": {
    "recommended": [                       // §2.5.4 — GUIDs chosen on prep night
      { "id": "d4f940ab-401b-4efc-aadc-ad5f3c50688a", "name": "Block Office apps from creating child processes" }
    ]
  },
  "entries": [
    {
      "id": "chrome",                      // stable key, used in tests
      "display_name": "Google Chrome",
      "match": {
        "name_regex": "^Google Chrome$",   // Python re, case-insensitive
        "publisher_regex": "^Google"       // optional
      },
      "min_safe_version": "131.0.0.0",     // FILL ON PREP NIGHT from vendor release notes
      "severity": "high",                  // high | medium  (§2.5.3)
      "eol": false,                        // true = no longer supported at any version
      "eol_note": null,
      "update_hint": "Open Chrome → Settings → About Chrome. It updates itself; then click Relaunch.",
      "source_url": "https://chromereleases.googleblog.com/"
    }
  ]
}
```

| Field | Type | Req? | Meaning |
|---|---|---|---|
| `baseline_version` | string (date) | ✅ | Version label shown in reports |
| `checked_on` | string (date) | ✅ | When the versions were researched |
| `os.min_supported_build.win11` | string | ✅ | Oldest Windows 11 build still serviced |
| `os.win10_eos_date` | string (date) | ✅ | Windows 10 end of support |
| `asr.recommended[]` | `{id, name}` | ✅ | ASR rules the engine expects |
| `entries[].id` | string | ✅ | Stable key |
| `entries[].display_name` | string | ✅ | Name in report |
| `entries[].match.name_regex` | string | ✅ | Match on `software.installed[].name` |
| `entries[].match.publisher_regex` | string | ⬜ | Disambiguates similar names |
| `entries[].min_safe_version` | string | ✅ | Below this = outdated |
| `entries[].severity` | `high`\|`medium` | ✅ | §2.5.3 S3/S4 |
| `entries[].eol` | boolean | ✅ | Product unsupported (§2.5.3 S2) |
| `entries[].update_hint` | string | ✅ | One-line fix step, used in `update-outdated-apps` |
| `entries[].source_url` | string | ✅ | Where the version came from (for judges' questions) |

**Default starter list (≥ 10 entries, [MVP]):** Chrome, Edge, Firefox, Adobe Acrobat Reader, 7-Zip, WinRAR, Zoom, Java (Oracle JRE), VLC, Microsoft Office/365, AnyDesk, TeamViewer. Rationale: common on SMME PCs and frequently exploited or abused by ransomware operators. Version numbers are filled in at home from each vendor's release page — the shipped product does no live lookups (MVP cut list).

### 2.9 Fix catalogue

Defined once in `scoring/fixes.py`; `steps` are plain English, 1–5 items, written for a non-technical owner-manager.

| Fix id | Category | Severity | `effort_minutes` | `needs_admin` |
|---|---|---|---|---|
| `enable-defender` | protection | red | 5 | ✅ |
| `update-defender-definitions` | protection | red/amber | 5 | ⬜ |
| `turn-on-bitlocker` | protection | red | 20 | ✅ |
| `encrypt-device-home` | protection | amber | 15 | ✅ |
| `enable-tamper-protection` | protection | amber | 3 | ✅ |
| `enable-cfa` | protection | amber | 5 | ✅ |
| `enable-asr-rules` | protection | amber | 15 | ✅ |
| `turn-on-file-history` | backup | red/amber | 15 | ⬜ |
| `run-backup-now` | backup | amber | 10 | ⬜ |
| `verify-backup-agent` | backup | amber | 10 | ⬜ |
| `install-updates` | patch | red/amber | 30 | ✅ |
| `restart-to-finish-updates` | patch | amber | 10 | ⬜ |
| `plan-windows-11` | patch | amber | 60 | ✅ |
| `update-outdated-apps` | software | red/amber | 20 | ⬜ |
| `enable-winre` | recovery | amber/red | 10 | ✅ |
| `turn-on-system-restore` | recovery | amber/red | 5 | ✅ |
| `create-restore-point` | recovery | amber | 5 | ✅ |

A fix's `severity` in `report.json` is the severity of the worst rule that attached it in this run.

### 2.10 Unit tests

**`tests/conftest.py`** — every test starts from the healthy fixture and overrides only what it is testing.

```python
# engine/tests/conftest.py
import copy, json
from pathlib import Path
import pytest
from antigravity_engine.parser import parse_dict
from antigravity_engine.baseline import load_baseline

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "shared" / "fixtures"

def _deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

@pytest.fixture(scope="session")
def healthy_raw() -> dict:
    return json.loads((FIXTURES / "scan.healthy.json").read_text(encoding="utf-8"))

@pytest.fixture
def make_scan(healthy_raw):
    """make_scan({"patch": {"days_since_latest_hotfix": 70}}) -> ScanModel"""
    def _make(patch: dict | None = None):
        return parse_dict(_deep_merge(healthy_raw, patch or {}))
    return _make

@pytest.fixture(scope="session")
def baseline():
    return load_baseline(ROOT / "baseline" / "software-baseline.json")
```

**Example tests per category** (one file each; trimmed to the essential cases):

```python
# engine/tests/test_backup.py
from antigravity_engine.scoring import backup

def test_recent_file_history_is_green(make_scan):
    r = backup.score(make_scan())               # healthy: FH 1 day old
    assert r.status == "green"

def test_onedrive_only_is_amber_not_green(make_scan):
    s = make_scan({"backup": {"file_history_enabled": False, "file_history_last_backup": None,
                              "shadow_copy_count": 0, "third_party_agents": []}})
    r = backup.score(s)                          # KFM still present in healthy fixture
    assert r.status == "amber" and "turn-on-file-history" in r.fix_ids

def test_no_evidence_is_red(make_scan):
    s = make_scan({"backup": {"file_history_enabled": False, "file_history_last_backup": None,
                              "onedrive_kfm_folders": [], "shadow_copy_count": 0,
                              "third_party_agents": []}})
    assert backup.score(s).status == "red"

def test_old_backup_over_30_days_is_red(make_scan):
    s = make_scan({"backup": {"file_history_last_backup": "2026-09-01T22:00:00Z"}})
    assert backup.score(s).status == "red"
```

```python
# engine/tests/test_patch.py
import pytest
from antigravity_engine.scoring import patch

@pytest.mark.parametrize("latest,expected", [
    ("2026-11-05", "green"),   # 9 days before collected_at 2026-11-14
    ("2026-10-15", "green"),   # 30 days — boundary is inclusive green
    ("2026-10-14", "amber"),   # 31 days
    ("2026-09-15", "amber"),   # 60 days
    ("2026-09-14", "red"),     # 61 days — stale hotfix
])
def test_30_60_heuristic(make_scan, latest, expected):
    s = make_scan({"patch": {"latest_hotfix_installed_on": latest}})
    assert patch.score(s).status == expected

def test_engine_recomputes_days_ignoring_collector_value(make_scan):
    s = make_scan({"patch": {"latest_hotfix_installed_on": "2026-08-01",
                             "days_since_latest_hotfix": 3}})   # collector lied/bugged
    assert patch.score(s).status == "red"

def test_pending_reboot_downgrades_green(make_scan):
    s = make_scan({"patch": {"pending_reboot": True}})
    assert patch.score(s).status == "amber"

def test_windows10_is_at_least_amber(make_scan):
    s = make_scan({"host": {"os_build": "19045", "os_caption": "Microsoft Windows 10 Pro"}})
    r = patch.score(s)
    assert r.status == "amber" and "plan-windows-11" in r.fix_ids

def test_no_hotfixes_is_red(make_scan):
    s = make_scan({"patch": {"hotfix_count": 0, "latest_hotfix_installed_on": None,
                             "days_since_latest_hotfix": None, "hotfixes": []}})
    assert patch.score(s).status == "red"
```

```python
# engine/tests/test_software.py
from antigravity_engine.scoring import software

def _with(make_scan, apps):
    return make_scan({"software": {"installed": apps}})

def test_outdated_high_severity_is_red(make_scan, baseline):
    s = _with(make_scan, [{"name": "Google Chrome", "version": "118.0.5993.118", "publisher": "Google LLC"}])
    assert software.score(s, baseline).status == "red"

def test_software_absent_from_baseline_is_not_assessed(make_scan, baseline):
    s = _with(make_scan, [{"name": "Pastel Partner", "version": "1.0", "publisher": "Sage"}])
    r = software.score(s, baseline)
    assert r.status == "green"
    assert any("not on our watch list" in row.value for row in r.evidence)

def test_unparseable_version_does_not_crash(make_scan, baseline):
    s = _with(make_scan, [{"name": "Google Chrome", "version": "latest", "publisher": "Google LLC"}])
    r = software.score(s, baseline)
    assert r.status in {"green", "amber"}

def test_empty_list_is_amber(make_scan, baseline):
    assert software.score(_with(make_scan, []), baseline).status == "amber"
```

```python
# engine/tests/test_protection.py
from antigravity_engine.scoring import protection

def test_bitlocker_off_on_pro_is_red(make_scan, baseline):
    s = make_scan({"protection": {"bitlocker": {"os_volume_protection": "off",
                                                "os_volume_encryption_pct": 0}}})
    r = protection.score(s, baseline)
    assert r.status == "red" and "turn-on-bitlocker" in r.fix_ids

def test_missing_bitlocker_on_home_is_amber_not_grey(make_scan, baseline):
    s = make_scan({"host": {"os_edition": "Core"},
                   "protection": {"bitlocker": {"status": "unavailable",
                                                "error": "BitLocker management not available on Windows Home",
                                                "os_volume_protection": None,
                                                "os_volume_encryption_pct": None}}})
    r = protection.score(s, baseline)
    assert r.status == "amber" and "encrypt-device-home" in r.fix_ids

def test_bitlocker_unavailable_non_admin_is_grey_row_only(make_scan, baseline):
    s = make_scan({"host": {"is_admin": False},
                   "protection": {"bitlocker": {"status": "unavailable", "error": "Requires administrator rights",
                                                "os_volume_protection": None}}})
    r = protection.score(s, baseline)
    assert r.status == "green"            # other sub-checks healthy
    assert any(row.status == "unavailable" for row in r.evidence)

def test_defender_service_stopped_is_red(make_scan, baseline):
    s = make_scan({"protection": {"defender": {"antivirus_enabled": False,
                                               "realtime_enabled": False,
                                               "third_party_av": None}}})
    assert protection.score(s, baseline).status == "red"

def test_third_party_av_is_not_penalised(make_scan, baseline):
    s = make_scan({"protection": {"defender": {"antivirus_enabled": False, "realtime_enabled": False,
                                               "third_party_av": "ESET Security"}}})
    r = protection.score(s, baseline)
    assert "enable-defender" not in r.fix_ids

def test_cfa_off_alone_is_amber(make_scan, baseline):
    s = make_scan({"protection": {"cfa": {"mode": "disabled"}}})
    assert protection.score(s, baseline).status == "amber"
```

```python
# engine/tests/test_recovery.py
from antigravity_engine.scoring import recovery

def test_healthy_is_green(make_scan):
    assert recovery.score(make_scan()).status == "green"

def test_no_winre_and_no_restore_points_is_red(make_scan):
    s = make_scan({"recovery": {"winre_enabled": False, "restore_point_count": 0}})
    assert recovery.score(s).status == "red"

def test_non_admin_nulls_stay_green_with_grey_rows(make_scan):
    s = make_scan({"host": {"is_admin": False},
                   "recovery": {"winre_enabled": None, "restore_point_count": None,
                                "latest_restore_point": None}})
    r = recovery.score(s)
    assert r.status == "green"
    assert sum(row.status == "unavailable" for row in r.evidence) >= 2
```

**Cross-cutting tests**

| File | Case | Asserts |
|---|---|---|
| `test_ranking.py` | Defender off + 70-day patch + no backup | `top_fixes == ["enable-defender", "turn-on-file-history", "install-updates"]` (red → category order) |
| `test_ranking.py` | All green | `top_fixes == []` |
| `test_fixtures.py` | Each `/shared/fixtures/scan.*.json` | `report.json` validates against `report.schema.json`; RAG matches the "expected" note in §0.7 |
| `test_cli.py` | `--in` points at a text file | exit code 2; `report.json` exists with 5 × `failed` |
| `test_cli.py` | `schema_version: "2.0.0"` | exit code 2 |
| `test_cli.py` | `protection` section `status: failed` | protection `failed`, others rated, exit 0 |
| `test_render.py` | Each fixture rendered | PDF starts with `%PDF` and has exactly one page; an app name containing `<script>` appears escaped in `report.html` |
| `test_integrity.py` | All fixtures | `unavailable` never becomes `failed`; red/amber categories have evidence and fixes; `top_fixes` ⊆ `fixes[]`, ≤ 3 (§7.6) |

Run:

```powershell
# cwd: antigravity/engine
.venv\Scripts\python -m pytest -q
```

### 2.11 Running the engine standalone

CLI (`antigravity_engine/__main__.py`):

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--in PATH` | ✅ | — | `scan.json` to read |
| `--out DIR` | ✅ | — | Folder for `report.json`, `report.html`, `action-plan.pdf` (created if missing) |
| `--baseline PATH` | ⬜ | `../baseline/software-baseline.json` relative to the exe/package | Baseline file |
| `--json-only` | ⬜ | off | Skip HTML/PDF (fast UI iteration) |
| `--version` | ⬜ | — | Print engine + contract version, exit 0 |

| Exit code | Meaning | `report.json` written? |
|---|---|---|
| 0 | Success (individual categories may still be `failed`) | ✅ |
| 2 | Invalid input (§2.4) | ✅ (all `failed`) |
| 3 | Rendering failed (HTML or PDF) | ✅ — UI shows results, disables "Open PDF" |
| 1 | Anything else (crash before writing) | ⬜ |

Steps:

1. Run from source against a fixture:
   ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\python -m antigravity_engine --in ..\shared\fixtures\scan.defender-off.json --out ..\out\defender-off
   ```
2. Check the exit code:
   ```powershell
   # cwd: antigravity/engine
   $LASTEXITCODE
   ```
3. Open the outputs:
   ```powershell
   # cwd: antigravity
   start out\defender-off\report.html; start out\defender-off\action-plan.pdf
   ```
4. Run against a **real** scan from Brick B's collector on your machine:
   ```powershell
   # cwd: antigravity
   powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -OutputPath out\me\scan.json
   engine\.venv\Scripts\python -m antigravity_engine --in out\me\scan.json --out out\me
   ```
5. Regenerate the UI fixtures for Frank after any rule change:
   ```powershell
   # cwd: antigravity/engine
   foreach ($f in Get-ChildItem ..\shared\fixtures\scan.*.json) {
     $name = $f.BaseName -replace '^scan\.', ''
     .venv\Scripts\python -m antigravity_engine --in $f.FullName --out ..\out\$name --json-only
     Copy-Item ..\out\$name\report.json ..\shared\fixtures\report.$name.json
   }
   ```
   Commit the changed `report.*.json` files in the same PR as the rule change.

### 2.12 PyInstaller build and no-Python verification

**Default:** one-folder build (`dist/engine/engine.exe` + `_internal/`). Rationale: starts in under a second (one-file builds unpack to `%TEMP%` on every run, adding seconds and occasionally triggering antivirus heuristics).

1. Create `engine/engine.spec`:
   ```python
   # engine/engine.spec
   from pathlib import Path
   ROOT = Path(SPECPATH).parent
   a = Analysis(
       ["antigravity_engine/__main__.py"],
       pathex=[str(Path(SPECPATH))],
       datas=[
           ("antigravity_engine/templates", "antigravity_engine/templates"),
           (str(ROOT / "shared/contract/scan.schema.json"), "contract"),
           (str(ROOT / "shared/contract/report.schema.json"), "contract"),
           (str(ROOT / "baseline/software-baseline.schema.json"), "contract"),
       ],
       hiddenimports=[],
       excludes=["tkinter", "unittest", "pytest"],
   )
   pyz = PYZ(a.pure)
   exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="engine",
             console=True, upx=False)
   coll = COLLECT(exe, a.binaries, a.datas, name="engine", upx=False)
   ```
   `upx=False` because UPX-compressed binaries are a common antivirus false-positive trigger.
2. In code, resolve bundled files through one helper:
   ```python
   # antigravity_engine/paths.py
   import sys
   from pathlib import Path
   def resource(rel: str) -> Path:
       base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
       return base / rel
   ```
3. Build:
   ```powershell
   # cwd: antigravity/engine
   .venv\Scripts\pyinstaller engine.spec --clean --noconfirm
   ```
4. Smoke test on your own machine:
   ```powershell
   # cwd: antigravity/engine
   dist\engine\engine.exe --version
   dist\engine\engine.exe --in ..\shared\fixtures\scan.healthy.json --out ..\out\exe-test --baseline ..\baseline\software-baseline.json
   ```
5. **Verify on a machine without Python** — pick one:
   - **Windows Sandbox (fastest, Windows Pro):** enable once with `Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM` (elevated, at home, needs reboot). Open Windows Sandbox, copy in `dist\engine\`, `baseline\` and one fixture, then run step 4's commands inside it.
   - **Schwan's clean VM** (§1.2 step 13): same copy-and-run.
6. In the clean environment, confirm Python is genuinely absent: `where python` must print nothing, or only the Microsoft Store alias stub.
7. Pass criteria: `--version` prints, `report.json` / `report.html` / `action-plan.pdf` all exist, the PDF opens, total run < 5 s.
8. Hand `dist\engine\` to Schwan only from a commit on `main` (§1.9).

### 2.13 Brick A is done when…

- [ ] `pytest -q` passes with ≥ 1 test per rule in §2.5 and every case in §2.10.
- [ ] All 4 `/shared/fixtures/scan.*.json` produce the expected RAG and schema-valid `report.json`.
- [ ] `report.*.json` UI fixtures regenerated and committed (§2.11 step 5).
- [ ] Bad input → exit 2 with an all-`failed` report; no traceback dialog.
- [ ] Baseline has ≥ 10 entries with real `min_safe_version` values and `source_url`s, researched at home.
- [ ] `engine.exe` runs in Windows Sandbox / clean VM with no Python, < 5 s.
- [ ] No network imports (`requests`, `urllib.request`, `http.client`) anywhere — check with `Select-String -Path engine\antigravity_engine\**\*.py -Pattern 'requests|urllib.request|http.client'` (cwd: `antigravity`) returning nothing.
- [ ] A second team member ran steps 1–3 of §2.11 from a fresh clone.

---

## §3 Brick B: Windows Collector (Shakir)

The collector is a PowerShell 5.1 script that reads system state and writes exactly one file: `scan.json` matching §0.5. License verification is also Shakir's, but it lives in Electron main, not the collector (§3.11).

### 3.1 Folder layout

Refines `/collector` from §1.7. New files ✚.

```
collector/
├── collector.ps1               entry point (§3.2, §3.3)
├── lib/
│   ├── Common.ps1              Invoke-Probe, ConvertTo-IsoUtc, Get-AgHash, Write-ScanJson
│   └── Allowlist.ps1       ✚   list of permitted cmdlets/exes for Test-ReadOnly
├── probes/
│   ├── Host.ps1            ✚   host block
│   ├── Backup.ps1
│   ├── Patch.ps1
│   ├── Software.ps1
│   ├── Protection.ps1
│   └── Recovery.ps1
├── mocks/                  ✚   §3.10
│   ├── home-edition.ps1
│   ├── defender-off.ps1
│   ├── non-admin.ps1
│   ├── stale-patches.ps1
│   └── probe-throws.ps1
└── tests/
    ├── Test-Collector.ps1      isolation test
    ├── Test-ReadOnly.ps1       static scan (§3.7)
    └── Test-Schema.ps1     ✚   validates output via engine's validator
desktop/src/main/license/
├── verify.ts                   §3.11
└── verify.test.ts          ✚   §3.11
tools/                      ✚   (repo root) dev-only, never packaged
├── issue-license.mjs           §3.11
└── demo-tokens.txt             (git-ignored) issued tokens
```

### 3.2 Script structure: one entry script + dot-sourced probes

**Default: one entry script (`collector.ps1`) that dot-sources one plain `.ps1` file per category. No `.psm1` modules.**

| Option | Verdict | Why |
|---|---|---|
| Single 600-line script | ❌ | Merge conflicts at 03:00; can't test one category alone |
| PowerShell modules (`.psm1` + `.psd1`) | ❌ | `Import-Module` path resolution, module auto-loading quirks and manifest versioning add failure modes with no benefit for a script we ship ourselves |
| **Entry script + dot-sourced probe files** | ✅ | One file per category = one owner-friendly unit to test (`-Only`); dot-sourcing from `$PSScriptRoot` works under `-ExecutionPolicy Bypass` with no path setup |

`collector.ps1` skeleton:

```powershell
# collector/collector.ps1  — PowerShell 5.1, READ-ONLY. See §3.7.
[CmdletBinding()]
param(
    [string]   $OutputPath,
    [switch]   $DryRun,
    [ValidateSet('Host','Backup','Patch','Software','Protection','Recovery')]
    [string[]] $Only,
    [string]   $MockFile,
    [ValidatePattern('^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[0-9a-f]{4}$')]
    [string]   $RunId
)
$ErrorActionPreference = 'Stop'
$Version = '0.1.0'
$sw = [Diagnostics.Stopwatch]::StartNew()

. "$PSScriptRoot\lib\Common.ps1"
Get-ChildItem "$PSScriptRoot\probes\*.ps1" | ForEach-Object { . $_.FullName }
if ($MockFile) { . (Resolve-Path $MockFile) }   # overrides Get-Ag* functions (§3.10)

if (-not $DryRun -and -not $OutputPath) { Write-Error 'Use -OutputPath <file> or -DryRun'; exit 64 }

$collectedAt = [DateTime]::UtcNow
$scan = [ordered]@{
    schema_version    = '1.0.0'
    run_id            = if ($RunId) { $RunId } else { '{0}_{1}' -f $collectedAt.ToString("yyyy-MM-dd'T'HH-mm-ss'Z'"), (Get-Random -Maximum 65535).ToString('x4') }
    collected_at      = $null          # filled at end
    collector_version = $Version
    duration_ms       = $null
}
$probes = [ordered]@{
    host = { Get-AgHost }; backup = { Get-AgBackup }; patch = { Get-AgPatch }
    software = { Get-AgSoftware }; protection = { Get-AgProtection }; recovery = { Get-AgRecovery }
}
foreach ($key in $probes.Keys) {
    if ($Only -and ($Only -notcontains (Get-Culture).TextInfo.ToTitleCase($key))) { continue }
    if (-not $DryRun) { Write-Output "AG-PHASE:$key" }   # progress marker for the app (§4.8); never in -DryRun, where stdout is the JSON
    $scan[$key] = & $probes[$key]
}
$scan.collected_at = ConvertTo-IsoUtc ([DateTime]::UtcNow)
$scan.duration_ms  = [int]$sw.ElapsedMilliseconds

Write-ScanJson -Scan $scan -Path $OutputPath -DryRun:$DryRun
exit 0
```

Each `Get-Ag*` function returns an ordered hashtable shaped exactly like its §0.5 section, always including `status` and `error`.

### 3.3 Parameters: -OutputPath, -DryRun, -Only, -MockFile, -RunId

| Parameter | Type | Meaning | Used by |
|---|---|---|---|
| `-OutputPath <file>` | string | Write `scan.json` here (UTF-8, no BOM). Parent folder must exist — the app creates it; the collector does **not** create folders. | Electron main (§5) |
| `-DryRun` | switch | Print JSON to stdout, write nothing. | Dev, tests |
| `-Only <names>` | string[] | Run only listed probes; output is a **partial** document (fails schema on purpose) | Isolated testing (§3.9) |
| `-MockFile <file>` | string | Dot-source a mock that overrides low-level readers (§3.10) | Tests |
| `-RunId <id>` | string | Use this `run_id` instead of generating one, so the run folder created by the app matches `scan.json` (§0.5, §5.6 step 8). Must match `^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[0-9a-f]{4}$` | Electron main (§4.7) |

| Exit code | Meaning |
|---|---|
| 0 | JSON produced (some sections may be `failed`/`unavailable`) |
| 64 | Bad arguments |
| 70 | Could not write `-OutputPath` |

When writing to `-OutputPath`, the collector also prints one `AG-PHASE:<section>` line to stdout before each probe (§4.8).

Electron treats anything except 0 as "scan failed" and shows a retry screen. Only one of `-OutputPath` or `-DryRun` is needed; if both, `-DryRun` wins and nothing is written.

### 3.4 The probe wrapper

Every query goes through `Invoke-Probe`, which is what turns errors into the §0.9 statuses.

```powershell
# collector/lib/Common.ps1 (excerpt)
class AgUnavailable : System.Exception { AgUnavailable([string]$m) : base($m) {} }

function Invoke-Probe {
    param([scriptblock]$Body, [System.Collections.Specialized.OrderedDictionary]$Template)
    $result = [ordered]@{ status = 'ok'; error = $null }
    foreach ($k in $Template.Keys) { $result[$k] = $Template[$k] }   # all keys present, null defaults
    try {
        $data = & $Body
        foreach ($k in $data.Keys) { $result[$k] = $data[$k] }
    } catch [AgUnavailable] {
        $result.status = 'unavailable'; $result.error = $_.Exception.Message
    } catch {
        $result.status = 'failed'
        $result.error  = ($_.Exception.GetType().Name + ': ' + $_.Exception.Message)
        if ($result.error.Length -gt 200) { $result.error = $result.error.Substring(0,200) }
    }
    return $result
}

function Test-AgAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
```

Rules:
1. Throw `[AgUnavailable]::new('Requires administrator rights')` for **known** preconditions (not admin, Home edition, feature absent).
2. Let everything else throw normally → becomes `failed`.
3. For fields that need admin **inside** an otherwise-readable section, set the field to `$null` and carry on; do not mark the whole section unavailable (§0.9 rule 2).
4. Error strings must contain no paths, usernames or hostnames (POPIA, §0.5). Use fixed messages where possible.

### 3.5 Query reference per category

Exact reads, the field they fill (§0.6), admin requirement, and failure mode. All are read operations. Items marked **⚠ verify** have value encodings that must be confirmed on both dev machines on prep night (record the observed values in `docs/decisions.md`).

#### Host (`host` block)

| Field | Exact query | Admin? |
|---|---|---|
| `os_caption` | `(Get-CimInstance -ClassName Win32_OperatingSystem).Caption` | No |
| `os_build` | `(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild` | No |
| `os_edition` | `(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID` | No |
| `is_admin` | `Test-AgAdmin` (§3.4) | No |
| `ps_version` | `$PSVersionTable.PSVersion.ToString()` | No |
| `hostname_hash` | `Get-AgHash $env:COMPUTERNAME` → `'sha256:' + hex(SHA256(salt + name))`, salt = fixed constant in `Common.ps1` | No |

#### 1. Backup evidence (`backup`)

| Field | Exact query | Admin? | Notes |
|---|---|---|---|
| `file_history_enabled` | `(Get-Service -Name fhsvc -ErrorAction SilentlyContinue).StartType -ne 'Disabled'` **and** `Test-Path "$env:LOCALAPPDATA\Microsoft\Windows\FileHistory\Configuration\Config1.xml"` | No | Config file exists only once File History has been set up |
| `file_history_last_backup` | `(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\FileHistory' -ErrorAction SilentlyContinue).ProtectedUpToTime` → `[DateTime]::FromFileTimeUtc($v)` | No | **⚠ verify** value name/type on a machine with File History configured; null if absent |
| `windows_backup_last_success` | `Get-WinEvent -FilterHashtable @{ LogName='Microsoft-Windows-Backup'; Id=4 } -MaxEvents 1` → `.TimeCreated` | Yes (log ACL) | Event 4 = backup completed successfully. Locale-independent, unlike parsing `wbadmin` text. Non-admin → `$null`. No events → `$null` |
| `onedrive_kfm_folders` | `Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'` — for value names `Desktop`, `Personal`, `My Pictures`, include the **friendly name** (`Desktop`, `Documents`, `Pictures`) if the value contains `\OneDrive` | No | Emit names only, never the path (POPIA) |
| `shadow_copy_count` | `@(Get-CimInstance -ClassName Win32_ShadowCopy).Count` | Yes | Use CIM, not `vssadmin` (§3.7). Non-admin → `$null` |
| `third_party_agents` | `Get-Service` names/display names matched against a fixed list: `Veeam*`, `Acronis*`, `Macrium*`, `Backblaze*`, `Carbonite*`, `Datto*`, `*Synology*Active Backup*`, `CrashPlan*`, `IDrive*` → emit the friendly product name | No | Presence only — we can't see their last success |

#### 2. Patch status (`patch`)

| Field | Exact query | Admin? | Notes |
|---|---|---|---|
| `hotfixes`, `hotfix_count`, `latest_hotfix_installed_on` | `$hf = @(Get-HotFix \| Where-Object { $_.InstalledOn } \| Sort-Object InstalledOn -Descending)`; count = `@(Get-HotFix).Count`; take top 10 as `@{kb=$_.HotFixID; installed_on=$_.InstalledOn.ToString('yyyy-MM-dd')}` | No | `InstalledOn` can be null or locale-misparsed on some machines — drop nulls; if **all** are null, set latest to `$null` (engine → red P2 only if `hotfix_count` is also 0; else see note) |
| `days_since_latest_hotfix` | `[int]([DateTime]::UtcNow.Date - $latest.Date).TotalDays` | No | Convenience only; engine recomputes (§2.4) |
| `pending_reboot` | `(Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')` | No | `Test-Path` on registry is read-only |

Note: if `hotfix_count > 0` but every `InstalledOn` is null, throw `[AgUnavailable]::new('Update dates unreadable on this PC')` — honest grey beats a false red.

#### 3. Installed software (`software`)

| Step | Exact query | Admin? |
|---|---|---|
| Read 3 uninstall roots | `'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'`, `'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'`, `'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'` via `Get-ItemProperty -Path $root -ErrorAction SilentlyContinue` | No |
| Filter | keep where `DisplayName` non-empty **and** `SystemComponent -ne 1` **and** no `ParentKeyName` **and** `ReleaseType` not in `Update`, `Hotfix`, `Security Update` | — |
| Project | `@{ name = $_.DisplayName.Trim(); version = "$($_.DisplayVersion)".Trim(); publisher = "$($_.Publisher)".Trim() }` | — |
| Dedupe | `Sort-Object name, version -Unique` | — |
| Cap | max 500 entries | — |

**Never** use `Win32_Product` — querying it makes Windows Installer run a consistency check on every MSI package and can trigger repairs. That is a write side-effect (§3.7).

#### 4. Ransomware protections (`protection`)

**Defender**

| Field | Exact query | Admin? |
|---|---|---|
| `antivirus_enabled` | `$mp = Get-MpComputerStatus; $mp.AntivirusEnabled` | No |
| `realtime_enabled` | `$mp.RealTimeProtectionEnabled` | No |
| `tamper_protected` | `$mp.IsTamperProtected` | No |
| `signature_age_days` | `$mp.AntivirusSignatureAge` | No |
| (running mode, used internally) | `$mp.AMRunningMode` — `Normal`, `Passive Mode`, `EDR Block Mode`, etc. | No |
| `third_party_av` | `Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct` → first `displayName` not matching `Windows Defender`/`Microsoft Defender Antivirus` | No |

**CFA**

| Field | Exact query | Admin? |
|---|---|---|
| `mode` | `(Get-MpPreference).EnableControlledFolderAccess` → `0` disabled, `1` enabled, `2` audit, `3` block-disk-modification-only, `4` audit-disk-modification-only. Map `1`,`3` → `enabled`; `2`,`4` → `audit`; `0` → `disabled` | No |
| fallback | `HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access` value `EnableControlledFolderAccess` (policy), then `HKLM:\SOFTWARE\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access` | No |

**ASR**

| Field | Exact query | Admin? |
|---|---|---|
| `rules[]` | `$p = Get-MpPreference`; zip `$p.AttackSurfaceReductionRules_Ids` with `$p.AttackSurfaceReductionRules_Actions`; action `0` off, `1` block, `2` audit, `6` warn | No |
| fallback | `HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Windows Defender Exploit Guard\ASR\Rules` — value name = GUID, data = action | No |

If both sources are empty, emit `rules: []` with `status: ok` (no rules configured is a finding, not an error).

**BitLocker**

| Field | Exact query | Admin? |
|---|---|---|
| precondition | `EditionID -like 'Core*'` → throw `AgUnavailable('BitLocker management not available on Windows Home')` | No |
| `os_volume_protection`, `os_volume_encryption_pct`, `encryption_method` | `$v = Get-BitLockerVolume -MountPoint $env:SystemDrive`; `ProtectionStatus` (`On`/`Off` → `on`/`off`), `EncryptionPercentage`, `EncryptionMethod` | **Yes** |
| non-admin fallback (`os_volume_protection` only) | `(New-Object -ComObject Shell.Application).NameSpace("$env:SystemDrive\").Self.ExtendedProperty('System.Volume.BitLockerProtection')` → `1` = on, `2` = off, `3` = encrypting; other values → `$null` **⚠ verify** | No |
| if non-admin and fallback returns `$null` | throw `AgUnavailable('Requires administrator rights')` | — |

#### 5. Recovery readiness (`recovery`)

| Field | Exact query | Admin? | Notes |
|---|---|---|---|
| `winre_enabled` | `$out = & "$env:SystemRoot\System32\reagentc.exe" /info 2>&1`; match `Windows RE status:\s+Enabled` / `Disabled` | Yes | Text is localised: if neither matches, `$null`. Non-admin → `$null` |
| `system_restore_enabled` | `$sr = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore' -ErrorAction SilentlyContinue`; enabled when `RPSessionInterval -eq 1` and `DisableSR -ne 1` | No | **⚠ verify** on a machine where you've toggled System Protection |
| `restore_point_count`, `latest_restore_point` | `$rp = @(Get-ComputerRestorePoint)`; count; latest = `[Management.ManagementDateTimeConverter]::ToDateTime(($rp \| Sort-Object SequenceNumber)[-1].CreationTime)` | Yes | Non-admin → both `$null` |

### 3.6 Graceful "not available" handling

| Situation | Detection | Section result | What the engine then does (§2.5) |
|---|---|---|---|
| Not elevated | `Test-AgAdmin` false | Admin-only **fields** `$null`; sections stay `ok` | Grey evidence rows |
| BitLocker on Windows Home | `EditionID -like 'Core*'` | `bitlocker.status = unavailable` | Rated amber with Home-specific fix |
| BitLocker cmdlet missing | `Get-Command Get-BitLockerVolume -ErrorAction SilentlyContinue` is null | try COM fallback; else `unavailable` | Grey |
| Defender passive (third-party AV) | `AMRunningMode -ne 'Normal'` or SecurityCenter2 lists another product | Defender fields read normally; `third_party_av` set | Not penalised |
| Defender service stopped/removed | `Get-MpComputerStatus` throws; then `(Get-Service WinDefend -ErrorAction SilentlyContinue).Status -ne 'Running'` | `defender.status = ok`, `antivirus_enabled = false`, `realtime_enabled = false` — **a stopped service is a finding** | Red unless `third_party_av` |
| `Get-MpComputerStatus` throws while WinDefend is Running | unexpected | `defender.status = failed` | Grey-striped |
| CFA/ASR when Defender isn't primary | `third_party_av` set | Read anyway; engine ignores | Excluded from rating |
| File History never configured | config file absent | `file_history_enabled = false`, last = `$null`, `status = ok` | Absence is the finding |
| Backup event log missing | `Get-WinEvent` throws "No events were found" or log not found | `windows_backup_last_success = $null`, `status = ok` | — |
| Non-English Windows | `reagentc` text doesn't match | `winre_enabled = $null` | Grey row |
| Constrained Language Mode | `$ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage'` | COM fallback and .NET calls skipped; write uses `Set-Content -Encoding UTF8` fallback (accept BOM; engine strips it in this one case) | **[STRETCH]** handle fully; MVP: document as known limitation |

### 3.7 Read-only guarantee

The collector **NEVER**:

1. Calls any cmdlet with verbs `Set-`, `New-`, `Remove-`, `Add-`, `Clear-`, `Enable-`, `Disable-`, `Start-`, `Stop-`, `Restart-`, `Suspend-`, `Resume-`, `Install-`, `Uninstall-`, `Update-`, `Register-`, `Unregister-`, `Invoke-WebRequest`, `Invoke-RestMethod`.
2. Writes to the registry, or changes any service, scheduled task, firewall rule or Defender preference.
3. Queries `Win32_Product` (triggers MSI consistency repairs, §3.5).
4. Runs `vssadmin`, `wbadmin start`, `manage-bde -on/-off`, `reagentc /enable`/`/disable`, `Checkpoint-Computer`, `bcdedit`, or any external exe outside the allow-list (`reagentc.exe /info` only).
5. Creates files or folders, except writing `-OutputPath` itself.
6. Changes execution policy or elevates itself (no `runas`, no UAC prompt).
7. Opens a network connection of any kind.
8. Reads user document contents, browser data, email, or credentials.
9. Records usernames, file paths, IP/MAC addresses, serial numbers or raw hostnames (§0.5 POPIA).
10. Installs anything, persists anything, or leaves a process running after exit.

Enforced by `tests/Test-ReadOnly.ps1`, which parses every `.ps1` in `collector/` with the PowerShell AST and fails on any command not in `lib/Allowlist.ps1`:

```powershell
# collector/tests/Test-ReadOnly.ps1
. "$PSScriptRoot\..\lib\Allowlist.ps1"     # defines $AgAllowedCommands (array of names)
$bad = @()
Get-ChildItem "$PSScriptRoot\..\" -Recurse -Filter *.ps1 |
  Where-Object { $_.FullName -notmatch '\\(tests|mocks)\\' } |
  ForEach-Object {
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$null, [ref]$null)
    $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.CommandAst] }, $true) |
      ForEach-Object {
        $name = $_.GetCommandName()
        if ($name -and $name -notin $AgAllowedCommands -and $name -notlike 'Get-Ag*' -and $name -notlike 'Invoke-Probe') {
          $bad += "$($_.Extent.File):$($_.Extent.StartLineNumber) $name"
        }
      }
    if (Select-String -Path $_.FullName -Pattern 'Win32_Product|vssadmin|wbadmin\s+start|manage-bde' -Quiet) {
      $bad += "$($_.Name): forbidden literal"
    }
  }
if ($bad) { $bad | Write-Host -ForegroundColor Red; exit 1 } else { Write-Host 'READ-ONLY OK'; exit 0 }
```

`Allowlist.ps1` contains exactly: `Get-CimInstance`, `Get-ItemProperty`, `Get-ChildItem`, `Get-Service`, `Get-HotFix`, `Get-MpComputerStatus`, `Get-MpPreference`, `Get-BitLockerVolume`, `Get-ComputerRestorePoint`, `Get-WinEvent`, `Get-Command`, `Get-Random`, `Get-Culture`, `Test-Path`, `Where-Object`, `ForEach-Object`, `Sort-Object`, `Select-Object`, `Resolve-Path`, `ConvertTo-Json`, `Write-Error`, `Write-Output`, `New-Object` (COM read fallback only — reviewed by hand), `reagentc.exe`. Adding to it requires Tshedi's review.

### 3.8 Writing scan.json correctly in PowerShell 5.1

Four 5.1 traps that silently break the contract:

| Trap | Symptom | Fix (in `Write-ScanJson` / helpers) |
|---|---|---|
| `ConvertTo-Json` default depth is 2 | Nested objects become `"System.Collections.Hashtable"` | Always `ConvertTo-Json -Depth 8` |
| Single-item arrays collapse to scalars | `"hotfixes": {…}` instead of `[{…}]` | Wrap every array: `@( … )` and assign with `-InputObject`, e.g. `ConvertTo-Json -InputObject $scan -Depth 8` |
| `DateTime` serialises as `"\/Date(…)\/"` | Engine rejects | Convert every date first with `ConvertTo-IsoUtc` → `$d.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")` |
| `Out-File -Encoding utf8` writes a BOM | §0.5 says no BOM | `[IO.File]::WriteAllText($Path, $json, (New-Object Text.UTF8Encoding $false))` |

```powershell
# collector/lib/Common.ps1 (excerpt)
function ConvertTo-IsoUtc([Nullable[DateTime]]$d) {
    if ($null -eq $d) { return $null }
    $d.Value.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
}
function Write-ScanJson($Scan, [string]$Path, [switch]$DryRun) {
    $json = ConvertTo-Json -InputObject $Scan -Depth 8
    if ($DryRun) { Write-Output $json; return }
    try { [IO.File]::WriteAllText($Path, $json, (New-Object Text.UTF8Encoding $false)) }
    catch { Write-Error "Cannot write output"; exit 70 }
}
```

### 3.9 Testing on two dev machines

Two deliberately different machines, assigned on prep night:

| | **Dev-1 "Healthy"** (Shakir) | **Dev-2 "Messy"** (Frank or Schwan) |
|---|---|---|
| OS | Windows 11 Pro | Windows 10 Pro, or Windows 11 **Home** if anyone has one |
| Run as | Admin and non-admin | Non-admin by default |
| Defender | On, Tamper on | Third-party AV if available, else Defender |
| BitLocker / Device Encryption | On | Off / Home |
| File History | Configured | Never configured |

Steps for each probe (repeat on both machines, normal and elevated PowerShell):

1. Run one probe alone:
   ```powershell
   # cwd: antigravity/collector
   powershell -NoProfile -ExecutionPolicy Bypass -File .\collector.ps1 -Only Protection -DryRun
   ```
2. Compare each field against the Windows Security / Settings UI by eye and note mismatches.
3. Time it: the `-Only` output still includes `duration_ms`. Target per probe: < 8 s; total < 20 s.
4. Run the full collector and validate against the contract via the engine's parser:
   ```powershell
   # cwd: antigravity
   powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -OutputPath out\dev\scan.json
   engine\.venv\Scripts\python -c "from antigravity_engine.parser import parse_path; parse_path(r'out\dev\scan.json'); print('VALID')"
   ```
5. Save the real outputs as private test data in `out/` (git-ignored) — **never commit real scans**, even hashed.

Safe state changes for testing (done **by a human, on dev machines only, then reverted** — the collector never does these):

| To test… | Change on dev machine | Revert |
|---|---|---|
| Defender real-time off | Windows Security → Virus & threat protection → Manage settings → Tamper Protection Off, then Real-time Off | Turn both back on (real-time re-enables itself after a while anyway) |
| CFA modes | Windows Security → Ransomware protection → Controlled folder access On/Off | Restore original |
| Pending reboot | Install any update and don't restart | Restart |
| System Restore off | System Properties → System Protection → C: → Configure → Disable | Re-enable |

Anything harder (BitLocker off, Home edition, old hotfixes) is tested with mocks (§3.10), not by changing a real machine.

### 3.10 Faking missing data

Probes never call system cmdlets directly for values they score. They call thin readers in `Common.ps1` (`Read-AgMpStatus`, `Read-AgHotFix`, `Read-AgBitLocker`, `Read-AgEdition`, `Test-AgAdmin`, …). A mock file redefines those readers; because `-MockFile` is dot-sourced after the probes (§3.2), the mock wins.

```powershell
# collector/mocks/home-edition.ps1
function Read-AgEdition { 'Core' }
function Read-AgOsCaption { 'Microsoft Windows 11 Home' }

# collector/mocks/defender-off.ps1
function Read-AgMpStatus { throw 'Service not running' }
function Read-AgServiceStatus([string]$Name) { if ($Name -eq 'WinDefend') { 'Stopped' } else { 'Running' } }

# collector/mocks/stale-patches.ps1
function Read-AgHotFix { @([pscustomobject]@{ HotFixID = 'KB5000001'; InstalledOn = (Get-Date).AddDays(-75) }) }

# collector/mocks/non-admin.ps1
function Test-AgAdmin { $false }

# collector/mocks/probe-throws.ps1
function Read-AgUninstallKeys { throw [System.IO.IOException]::new('simulated registry failure') }
```

Run a mock:

```powershell
# cwd: antigravity/collector
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector.ps1 -DryRun -MockFile .\mocks\home-edition.ps1
```

`tests/Test-Collector.ps1` runs the collector once with no mock and once per mock file, then asserts:

| Mock | Expected |
|---|---|
| none | All sections present; output schema-valid |
| `home-edition` | `protection.bitlocker.status == 'unavailable'`, error mentions Home |
| `defender-off` | `protection.defender.status == 'ok'`, `antivirus_enabled == $false` |
| `stale-patches` | `patch.days_since_latest_hotfix -ge 75` |
| `non-admin` | `backup.shadow_copy_count`, `recovery.restore_point_count` are `$null`; all statuses `ok` |
| `probe-throws` | `software.status == 'failed'`; other sections still `ok` |

Additionally, mock-generated outputs can be saved to `/shared/fixtures/` when they represent a new case for Brick A (via §0.10 if the case reveals a contract gap).

### 3.11 License token verification

**Where it lives — Default: Electron main process (`desktop/src/main/license/verify.ts`), not the collector.**

| Option | Verdict | Why |
|---|---|---|
| Collector (PowerShell) | ❌ | .NET Framework 4.x under PowerShell 5.1 has no built-in Ed25519; would need a bundled crypto DLL. Also mixes a gate into a read-only scanner. |
| Renderer (React) | ❌ | Renderer code is inspectable/alterable via DevTools; the check must sit where the scan is launched. |
| Engine (Python) | ❌ | Engine runs after the scan — too late to gate it, and it should stay pure. |
| **Electron main** | ✅ | Node's `node:crypto` verifies Ed25519 natively, no dependency; main owns the `scan:run` IPC handler so it can refuse to spawn the collector without a valid license. |

**Token format** (JWT-like, but our own and minimal):

```
AG1.<base64url(payload-json)>.<base64url(ed25519-signature)>
```

- Signature is over the ASCII bytes of `AG1.<payload-segment>` (prefix included, so a token can't be re-labelled).
- Payload:

```jsonc
{
  "v": 1,                      // token format version
  "kid": "demo-2026",          // which public key; app bundles a map kid → PEM
  "lic": "AG-DEMO-0001",       // licence id shown in the app footer
  "org": "HackSecure Judges",  // shown on the report header
  "tier": "demo",              // demo | pilot
  "iat": 1793750400,           // issued at, Unix seconds
  "nbf": 1793750400,           // not before
  "exp": 1795046400,           // expiry — demo keys: event end + 30 days
  "features": ["scan", "pdf"]
}
```

**Issuing (Shakir, at home, once)** — `tools/issue-license.mjs`, run with plain Node:

```js
// tools/issue-license.mjs   usage: node issue-license.mjs keygen | node issue-license.mjs sign "<org>" <licId> <days>
import { generateKeyPairSync, createPrivateKey, sign } from "node:crypto";
import { writeFileSync, readFileSync } from "node:fs";
const b64u = (b) => Buffer.from(b).toString("base64url");
const [cmd, org, lic, days] = process.argv.slice(2);
if (cmd === "keygen") {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  writeFileSync("../shared/license/public-key.pem", publicKey.export({ type: "spki", format: "pem" }));
  writeFileSync(process.env.USERPROFILE + "/.antigravity-private.pem",
                privateKey.export({ type: "pkcs8", format: "pem" }));   // NEVER in the repo
} else if (cmd === "sign") {
  const now = Math.floor(Date.now() / 1000);
  const payload = { v: 1, kid: "demo-2026", lic, org, tier: "demo", iat: now, nbf: now,
                    exp: now + Number(days) * 86400, features: ["scan", "pdf"] };
  const head = "AG1." + b64u(JSON.stringify(payload));
  const key = createPrivateKey(readFileSync(process.env.USERPROFILE + "/.antigravity-private.pem"));
  console.log(head + "." + b64u(sign(null, Buffer.from(head, "ascii"), key)));
}
```

1. ```powershell
   # cwd: antigravity/tools
   node issue-license.mjs keygen
   ```
2. Back up `%USERPROFILE%\.antigravity-private.pem` to a password manager. Never commit it.
3. Issue the 3 demo keys:
   ```powershell
   # cwd: antigravity/tools
   node issue-license.mjs sign "HackSecure Judges" AG-DEMO-0001 60
   node issue-license.mjs sign "Team Antigravity" AG-DEMO-0002 60
   node issue-license.mjs sign "Mentor Panel" AG-DEMO-0003 60
   ```
4. Paste the tokens into `shared/license/demo-keys.md` (they are public by design — they only unlock a free, local tool).
5. Issue one **already-expired** token (`days` = `-1`) for testing; keep it in `tools/demo-tokens.txt` (git-ignored).

**Verification steps in `verify.ts`** (each failure returns a distinct reason code):

| # | Step | On failure → reason |
|---|---|---|
| 1 | Trim whitespace; split on `.`; expect exactly 3 parts with prefix `AG1` | `malformed` |
| 2 | base64url-decode payload; `JSON.parse`; check required fields and types | `malformed` |
| 3 | Look up `kid` in bundled key map | `unknown_key` |
| 4 | `crypto.verify(null, Buffer.from("AG1."+p, "ascii"), publicKey, sigBytes)` | `bad_signature` |
| 5 | `now + 24h skew < nbf` | `not_yet_valid` |
| 6 | `now - 24h skew > exp` | `expired` |
| 7 | `features` includes `"scan"` | `not_entitled` |

```ts
// desktop/src/main/license/verify.ts
import { createPublicKey, verify as edVerify } from "node:crypto";
import publicPem from "../../../../shared/license/public-key.pem?raw";

export type LicenseResult =
  | { ok: true; lic: string; org: string; exp: number }
  | { ok: false; reason: "malformed" | "unknown_key" | "bad_signature" | "not_yet_valid" | "expired" | "not_entitled" };

const KEYS: Record<string, ReturnType<typeof createPublicKey>> = { "demo-2026": createPublicKey(publicPem) };
const SKEW = 24 * 3600;

export function verifyLicense(token: string, nowSec = Math.floor(Date.now() / 1000)): LicenseResult {
  const parts = token.trim().split(".");
  if (parts.length !== 3 || parts[0] !== "AG1") return { ok: false, reason: "malformed" };
  let p: any;
  try { p = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")); } catch { return { ok: false, reason: "malformed" }; }
  if (p?.v !== 1 || typeof p.kid !== "string" || typeof p.exp !== "number" || typeof p.nbf !== "number"
      || typeof p.lic !== "string" || !Array.isArray(p.features)) return { ok: false, reason: "malformed" };
  const key = KEYS[p.kid];
  if (!key) return { ok: false, reason: "unknown_key" };
  const good = edVerify(null, Buffer.from(`AG1.${parts[1]}`, "ascii"), key, Buffer.from(parts[2], "base64url"));
  if (!good) return { ok: false, reason: "bad_signature" };
  if (nowSec + SKEW < p.nbf) return { ok: false, reason: "not_yet_valid" };
  if (nowSec - SKEW > p.exp) return { ok: false, reason: "expired" };
  if (!p.features.includes("scan")) return { ok: false, reason: "not_entitled" };
  return { ok: true, lic: p.lic, org: String(p.org ?? ""), exp: p.exp };
}
```

(`?raw` imports are supported by electron-vite for main-process code. If that proves awkward, embed the PEM as a string constant generated at build time.)

**Behaviour in the app**

| Reason | Message to user | App behaviour |
|---|---|---|
| `malformed` | "That doesn't look like an Antigravity key. Check you copied all of it." | Stay on license screen |
| `unknown_key`, `bad_signature` | "This key isn't valid." (same message for both — don't help tamperers) | Stay; log reason locally |
| `expired` | "This key expired on {date}. Ask us for a new one." | Stay |
| `not_yet_valid` | "This key isn't active yet. Check your PC's date and time." | Stay |
| `not_entitled` | "This key doesn't include scanning." | Stay |
| ok | Footer shows `lic` and `org` | Save token to `%APPDATA%\Antigravity\license.txt`; re-verify on every launch **and** inside the `scan:run` handler before spawning the collector |

Tampering cases covered by tests (`verify.test.ts`, run in `/desktop` with `npm run test`): valid demo key → ok; one character changed in payload → `bad_signature`; signature segment swapped from another token → `bad_signature`; expired token → `expired`; `kid` changed → `unknown_key` or `bad_signature`; empty string → `malformed`.

Honest limitation (say it if judges ask): a purely offline check can be bypassed by someone who modifies the app binary. For a free local tool aimed at honest SMME owners that's acceptable; online activation is out of scope (MVP cut list).

### 3.12 Execution policy and code signing

| Topic | Decision | Rationale |
|---|---|---|
| How the app launches the collector | `powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "<resources>\collector\collector.ps1" -OutputPath "<run>\scan.json"` spawned from Node with `windowsHide: true` | Per-process bypass; no profile scripts interfering; no console flash |
| Absolute path to PowerShell | `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe` | Guarantees 5.1, avoids PATH hijack and `pwsh` 7 |
| Don't use `-WindowStyle Hidden` or `-EncodedCommand` | — | Both are classic malware patterns that Defender/EDR heuristics flag; `windowsHide` achieves the same quietly |
| Machine-wide policy set by Group Policy (`AllSigned`/`RemoteSigned` via GPO) | GPO policy overrides `-ExecutionPolicy Bypass` | Detect: if collector exits non-zero with "running scripts is disabled", UI shows "Your IT policy blocks scripts" — rare for our no-IT target, so **[MVP]** = clear message only |
| Mark-of-the-Web | NSIS-installed files don't carry the download zone mark; `Bypass` ignores it anyway | No action |
| Signing `collector.ps1` | **[STRETCH]** | Authenticode signing only helps with a cert from a trusted CA; a self-signed cert fails on judges' machines. Not worth it in 2 days |
| Signing the installer / `.exe`s | **[STRETCH]** — not for the hackathon | A trusted code-signing cert takes days to issue. Unsigned installer shows SmartScreen "Windows protected your PC" → **More info → Run anyway**. Rehearse this click in the demo; mention it in the pitch as a post-hackathon item |
| Defender scanning our PowerShell | Expect AMSI to scan the script; it's plain and read-only so it should pass | Schwan's clean-VM test (§1.5) must run with Defender **on** and real-time on, to catch any false positive before the judges do |
| Files packaged | `collector/` minus `tests/` and `mocks/` | electron-builder `extraResources` filter (configured in §5); mocks in a shipped build would be an attack surface |

### 3.13 Brick B is done when…

- [ ] `Test-ReadOnly.ps1` prints `READ-ONLY OK`.
- [ ] `Test-Collector.ps1` passes with no mock and with all 5 mocks (§3.10).
- [ ] Full run validates against `scan.schema.json` via the engine parser (§3.9 step 4) on **both** dev machines, elevated and not.
- [ ] Full collection < 20 s on both machines (budget for the 60 s scan target, §0.3).
- [ ] Every **⚠ verify** encoding in §3.5 confirmed and recorded in `docs/decisions.md`.
- [ ] Output contains no usernames, paths, IPs or raw hostnames — check with `Select-String -Path out\dev\scan.json -Pattern $env:USERNAME, $env:COMPUTERNAME` (cwd: `antigravity`) returning nothing.
- [ ] License: 3 demo tokens issued, private key backed up and not in Git, `verify.test.ts` passes all tamper cases, `scan:run` refuses without a valid license.
- [ ] Contract fixtures (§0.7) still match what the real collector produces; any drift fixed via §0.10 before 21:15 Day 1.

---

## §4 Brick C: Electron/React Frontend & Reports (Frank)

Frank owns everything the user sees: the desktop renderer, the look and copy of the HTML report and PDF, the landing page and the demo. The main-process plumbing (spawning, paths) is Schwan's (§5); license verification is Shakir's (§3.11). Frank codes only against `report.json` (§0.8) and the IPC contract (§4.6).

### 4.1 Folder layout

Refines `/desktop` and `/landing` from §1.7. New files ✚. Owner letter in brackets.

```
desktop/
├── package.json                        [C] §4.2
├── electron.vite.config.ts             [C]
├── electron-builder.yml                [D] §5.2
├── components.json                     [C] shadcn config
├── vitest.config.ts                    [C]
├── resources/icon.ico                  [C] 256×256 multi-size icon
└── src/
    ├── shared/
    │   └── ipc.ts                  ✚   [C+D] channel names + payload types (§4.6)
    ├── main/
    │   ├── index.ts                    [D] lifecycle, window, security flags (§4.4)
    │   ├── ipc.ts                      [D] handlers for every channel in §4.6
    │   ├── paths.ts                ✚   [D] dev vs packaged path resolution (§5.5)
    │   ├── runs.ts                 ✚   [D] create/clean run folders
    │   ├── mock.ts                 ✚   [C] AG_MOCK=1 fake scan (§4.12)
    │   ├── license/verify.ts           [B] §3.11
    │   ├── license/store.ts        ✚   [B] read/write license.txt
    │   └── pipeline/
    │       ├── runProcess.ts       ✚   [D] spawn wrapper: timeout, kill tree, line reader (§4.7)
    │       ├── runCollector.ts         [D] §4.7
    │       └── runEngine.ts            [D] §4.7
    ├── preload/index.ts                [D] contextBridge → window.antigravity (§4.6)
    └── renderer/
        ├── index.html                  [C] CSP meta tag (§4.4)
        └── src/
            ├── main.tsx                [C]
            ├── App.tsx                 [C] screen state machine (§4.9)
            ├── env.d.ts            ✚   [C] types for window.antigravity
            ├── styles/globals.css      [C] Tailwind + RAG tokens (§4.3)
            ├── lib/utils.ts            [C] cn()
            ├── lib/reportSchema.ts ✚   [C] zod schema mirroring §0.8
            ├── lib/progress.ts     ✚   [C] progress model (§4.8)
            ├── components/ui/          [C] shadcn generated
            ├── components/
            │   ├── StatusBadge.tsx     [C]
            │   ├── CategoryCard.tsx    [C]
            │   ├── EvidenceTable.tsx ✚ [C]
            │   ├── FixList.tsx         [C]
            │   └── AdminHint.tsx   ✚   [C]
            ├── screens/
            │   ├── LicenseScreen.tsx   [C]
            │   ├── ScanningScreen.tsx  [C]
            │   ├── ResultsScreen.tsx   [C]
            │   └── ErrorScreen.tsx ✚   [C]
            ├── mocks/
            │   └── report.all-states.json ✚ [C] §4.12
            └── __tests__/
                ├── fixtures.test.tsx   [C]
                └── progress.test.ts ✚  [C]
engine/antigravity_engine/
├── templates/report.html.j2            [C design, A wiring] §4.10
└── render/pdf.py                       [A code, C layout spec] §4.11
landing/                                [C] §4.13 (tree in §1.7)
```

Ownership of report rendering: the files live in the engine (so `engine.exe` produces all three outputs standalone, §2.11), **Frank owns the design and the words, Tshedi owns the code.** Pair on it for 30 minutes at Day 1 ~19:00.

### 4.2 package.json

Dependencies are unchanged from §1.10 (pins and reasons are there). Only `scripts` grew:

```json
{
  "name": "antigravity-desktop",
  "productName": "Antigravity",
  "version": "0.1.0",
  "private": true,
  "description": "Read-only cyber health check for small businesses",
  "author": "Team Antigravity",
  "main": "out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "typecheck": "tsc --noEmit -p tsconfig.node.json && tsc --noEmit -p tsconfig.web.json",
    "test": "vitest run",
    "dist:dir": "electron-vite build && electron-builder --win --dir",
    "dist": "electron-vite build && electron-builder --win nsis"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "3.0.1",
    "lucide-react": "0.471.0",
    "@radix-ui/react-slot": "1.1.1",
    "@radix-ui/react-progress": "1.1.1",
    "@radix-ui/react-separator": "1.1.1",
    "zod": "3.24.1"
  },
  "devDependencies": {
    "electron": "34.0.0",
    "electron-builder": "25.1.8",
    "electron-vite": "3.0.0",
    "vite": "6.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "typescript": "5.7.3",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "@types/node": "22.10.7",
    "tailwindcss": "4.0.0",
    "@tailwindcss/vite": "4.0.0",
    "tw-animate-css": "1.2.0",
    "vitest": "2.1.8",
    "@testing-library/react": "16.1.0",
    "jsdom": "25.0.1"
  }
}
```

| Script | Use |
|---|---|
| `dev` | Day-to-day development with hot reload |
| `typecheck` | Run before every PR |
| `test` | Isolation test (§4.14) |
| `dist:dir` | Unpacked build in `release/win-unpacked` — fast packaging check without NSIS (§5.8) |
| `dist` | Full installer (§5.8) |

**Default:** no `cross-env` or `concurrently`. Rationale: every extra dev dependency is one more thing to fetch offline; PowerShell sets env vars fine (§4.12).

### 4.3 Tailwind v4 + shadcn/ui setup

Initial setup is §1.2 steps 14–19 (done once by Frank, committed). Then:

1. Replace `desktop/src/renderer/src/styles/globals.css` with:
   ```css
   @import "tailwindcss";
   @import "tw-animate-css";

   /* RAG tokens — the only place status colours are defined (§4.10 uses the same hex values) */
   @theme {
     --color-rag-red: #b42318;
     --color-rag-red-bg: #fef3f2;
     --color-rag-amber: #b54708;
     --color-rag-amber-bg: #fffaeb;
     --color-rag-green: #067647;
     --color-rag-green-bg: #ecfdf3;
     --color-rag-grey: #475467;
     --color-rag-grey-bg: #f2f4f7;
     --font-sans: "Segoe UI", system-ui, sans-serif;
   }
   ```
   `Segoe UI` is on every Windows machine, so no font download is needed offline.
2. Keep the shadcn CSS variables that `shadcn init` added below these lines; don't edit them by hand.
3. Use the tokens as normal utilities: `text-rag-red bg-rag-red-bg`.
4. Never write a hex colour in a component. All RAG colour goes through `StatusBadge` (§4.9).

### 4.4 Main / preload / renderer split

| Layer | Runs as | Owner | May do | May NOT do |
|---|---|---|---|---|
| **Main** (`src/main`) | Node.js, full OS access | D (+ B for license) | Verify license, create run folders, spawn collector/engine, read `report.json`, open files with `shell.openPath` | Render UI |
| **Preload** (`src/preload`) | Isolated bridge | D | Expose a fixed list of functions via `contextBridge` | Expose `ipcRenderer`, `require`, or generic "invoke anything" |
| **Renderer** (`src/renderer`) | Chromium, sandboxed | C | Draw screens, call `window.antigravity.*`, validate `report.json` with zod | Touch the file system, spawn processes, see paths |

Who calls what:

```
Renderer ──window.antigravity.runScan()──▶ Preload ──ipc──▶ Main
                                                            ├─ verifyLicense()        [B]
                                                            ├─ runCollector()  → powershell.exe collector.ps1   [B code, D wiring]
                                                            └─ runEngine()     → engine.exe                      [A code, D wiring]
Renderer ◀──scan:progress events / ScanResult────────────── Main
```

Security settings (in `main/index.ts`, owner D, required):

| Setting | Value | Why |
|---|---|---|
| `contextIsolation` | `true` | Renderer can't reach preload internals |
| `nodeIntegration` | `false` | No Node in the renderer |
| `sandbox` | `true` | Chromium sandbox on |
| `webSecurity` | `true` | Default; never disable |
| Navigation | `win.webContents.on('will-navigate', e => e.preventDefault())`; `setWindowOpenHandler(() => ({ action: 'deny' }))` | App can't be navigated to a web page |
| CSP (`index.html`) | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'` | Renderer can't reach the network at all — matches "local-only" |
| Menu | `Menu.setApplicationMenu(null)` in packaged builds | No DevTools menu for users |
| Spellcheck | `webPreferences.spellcheck: false` | No dictionary downloads — nothing leaves the PC (PRV-11, §7.5) |

### 4.5 How the app runs the collector and engine

**Default: `child_process.spawn` of the bundled binaries from the main process, `shell: false`, arguments as an array.**

| Option | Verdict | Why |
|---|---|---|
| **`spawn` (argument array, no shell)** | ✅ | No shell = no quoting or injection issues with paths containing spaces; streams stdout so we can read phase markers (§4.8); exit codes map directly to §2.11 and §3.3; each brick stays a standalone CLI that can be tested alone |
| `exec` / `execFile` with `shell: true` | ❌ | Buffers output (no live progress); shell quoting bugs with `C:\Users\Thandi Mokoena\…` |
| Long-running local HTTP server (Python Flask/FastAPI) | ❌ | Opens a port (looks bad for a security product, may trigger firewall prompts), adds lifecycle bugs, needs more dependencies |
| Node PowerShell bindings / embedding Python | ❌ | Native modules complicate packaging; breaks brick isolation |
| `utilityProcess` (Electron) | ❌ | For Node scripts, not for external `.exe`/`.ps1` |

Files are the interface (§0.1): collector writes `scan.json`, engine reads it and writes `report.json`. Main only reads `report.json`.

### 4.6 IPC contract

Defined once in `desktop/src/shared/ipc.ts` and imported by main, preload and renderer.

```ts
// desktop/src/shared/ipc.ts
export const IPC = {
  licenseGet:    "license:get",      // invoke → LicenseState
  licenseSubmit: "license:submit",   // invoke(token) → LicenseState
  scanRun:       "scan:run",         // invoke → ScanResult   (long-running, resolves at end)
  scanCancel:    "scan:cancel",      // invoke → void
  scanProgress:  "scan:progress",    // main → renderer event: ScanProgress
  reportOpenPdf: "report:openPdf",   // invoke(runId) → { ok: boolean }
  reportOpenHtml:"report:openHtml",  // invoke(runId) → { ok: boolean }
  appInfo:       "app:info",         // invoke → AppInfo
} as const;

export type LicenseState =
  | { status: "none" }
  | { status: "valid"; lic: string; org: string; exp: number }
  | { status: "invalid"; reason: "malformed" | "unknown_key" | "bad_signature" | "not_yet_valid" | "expired" | "not_entitled" };

export type Phase = "starting" | "host" | "backup" | "patch" | "software" | "protection" | "recovery" | "engine" | "done";
export type ScanProgress = { runId: string; phase: Phase; elapsedMs: number };

export type ScanResult =
  | { ok: true;  runId: string; report: unknown; pdfAvailable: boolean }   // report validated in renderer with zod
  | { ok: false; runId: string; stage: "license" | "collector" | "engine" | "cancelled" | "timeout";
      message: string };                                                    // plain English, no paths

export type AppInfo = { version: string; isAdmin: boolean; mock: boolean };
```

Preload exposes exactly these functions:

```ts
// desktop/src/preload/index.ts
import { contextBridge, ipcRenderer } from "electron";
import { IPC, type ScanProgress } from "../shared/ipc";

contextBridge.exposeInMainWorld("antigravity", {
  getLicense:   () => ipcRenderer.invoke(IPC.licenseGet),
  submitLicense:(token: string) => ipcRenderer.invoke(IPC.licenseSubmit, token),
  runScan:      () => ipcRenderer.invoke(IPC.scanRun),
  cancelScan:   () => ipcRenderer.invoke(IPC.scanCancel),
  onProgress:   (cb: (p: ScanProgress) => void) => {
    const h = (_: unknown, p: ScanProgress) => cb(p);
    ipcRenderer.on(IPC.scanProgress, h);
    return () => ipcRenderer.removeListener(IPC.scanProgress, h);
  },
  openPdf:      (runId: string) => ipcRenderer.invoke(IPC.reportOpenPdf, runId),
  openHtml:     (runId: string) => ipcRenderer.invoke(IPC.reportOpenHtml, runId),
  appInfo:      () => ipcRenderer.invoke(IPC.appInfo),
});
```

Rules:
1. The renderer never sends a path. `openPdf(runId)` → main validates `runId` against `^[0-9TZ:-]+_[0-9a-f]{4}$` and builds the path itself.
2. Only one scan at a time; a second `scan:run` while running returns `{ ok: false, stage: "collector", message: "A scan is already running." }`.
3. `scan:run` re-verifies the license before spawning anything (§3.11).

### 4.7 Exact spawn calls

Shared wrapper (owner D):

```ts
// desktop/src/main/pipeline/runProcess.ts
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";

export type RunOpts = { cwd: string; timeoutMs: number; onLine?: (l: string) => void; signal?: AbortSignal };
export type RunOut  = { code: number | null; timedOut: boolean; cancelled: boolean; stderr: string };

export function runProcess(cmd: string, args: string[], o: RunOpts): Promise<RunOut> {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, { cwd: o.cwd, shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    let stderr = "", timedOut = false, cancelled = false;
    const killTree = () => {
      if (child.pid) spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], { windowsHide: true, shell: false });
    };
    const timer = setTimeout(() => { timedOut = true; killTree(); }, o.timeoutMs);
    o.signal?.addEventListener("abort", () => { cancelled = true; killTree(); });
    createInterface({ input: child.stdout! }).on("line", (l) => o.onLine?.(l));
    child.stderr!.on("data", (d) => { if (stderr.length < 4000) stderr += d.toString(); });
    child.on("close", (code) => { clearTimeout(timer); resolve({ code, timedOut, cancelled, stderr }); });
    child.on("error", (e) => { clearTimeout(timer); resolve({ code: -1, timedOut, cancelled, stderr: String(e) }); });
  });
}
```

`taskkill /T` kills the whole process tree (PowerShell plus any `reagentc.exe` child); `child.kill()` alone would leave grandchildren running on Windows.

**Collector call** (owner D, script by B):

```ts
// desktop/src/main/pipeline/runCollector.ts
import path from "node:path";
import { paths } from "../paths";
import { runProcess } from "./runProcess";

export function runCollector(runDir: string, runId: string, onLine: (l: string) => void, signal: AbortSignal) {
  const ps = path.join(process.env.SystemRoot ?? "C:\\Windows", "System32", "WindowsPowerShell", "v1.0", "powershell.exe");
  return runProcess(ps, [
    "-NoLogo", "-NoProfile", "-NonInteractive",
    "-ExecutionPolicy", "Bypass",
    "-File", paths.collectorScript(),          // …\resources\collector\collector.ps1
    "-OutputPath", path.join(runDir, "scan.json"),
    "-RunId", runId,                           // see §3.3
  ], { cwd: runDir, timeoutMs: 45_000, onLine, signal });
}
```

**Engine call** (owner D, engine by A):

```ts
// desktop/src/main/pipeline/runEngine.ts
import path from "node:path";
import { paths } from "../paths";
import { runProcess } from "./runProcess";

export function runEngine(runDir: string, signal: AbortSignal) {
  const { cmd, prefixArgs, cwd } = paths.engine();   // packaged: engine.exe; dev: python -m antigravity_engine (§5.5)
  return runProcess(cmd, [
    ...prefixArgs,
    "--in", path.join(runDir, "scan.json"),
    "--out", runDir,
    "--baseline", paths.baseline(),
  ], { cwd, timeoutMs: 15_000, signal });
}
```

Argument conventions:

| Convention | Rule |
|---|---|
| Paths | Always absolute, always passed as separate array items (never concatenated into one string) |
| Working directory | Collector: the run folder. Engine: the engine's own folder (so PyInstaller finds `_internal/`) |
| Timeouts | Collector 45 s + engine 15 s = 60 s worst case, matching the MVP "< 60 s" |
| Exit-code mapping | Collector ≠ 0 → `stage: "collector"`. Engine 0 → ok; 3 → ok with `pdfAvailable: false`; 2 → ok (report shows `failed` categories); anything else → `stage: "engine"` |
| Errors shown to users | Fixed plain-English messages from a table in `ipc.ts`; raw `stderr` goes only to `%LOCALAPPDATA%\Antigravity\logs\last-error.txt` |

### 4.8 Progress model

PowerShell 5.1 gives no progress events to a parent process, so we build a progress model from two signals:

1. **Phase markers.** The collector prints one line to stdout before each probe: `AG-PHASE:backup`, `AG-PHASE:patch`, … (§3.2). Main forwards each as a `scan:progress` event. Main adds `starting` (on spawn), `engine` (on engine spawn) and `done`.
2. **Time.** Between markers the bar keeps moving towards the next phase boundary based on elapsed time, so it never looks frozen.

Phase bands (weights tuned on Dev-1/Dev-2 timings from §3.9; update after measuring):

| Phase | Band (%) | Expected time | Message shown |
|---|---|---|---|
| `starting` | 0–4 | 1 s | "Starting the check…" |
| `host` | 4–8 | 1 s | "Looking at your Windows version…" |
| `backup` | 8–28 | 4 s | "Looking for backups…" |
| `patch` | 28–40 | 2 s | "Checking Windows updates…" |
| `software` | 40–55 | 2 s | "Checking installed apps…" |
| `protection` | 55–80 | 5 s | "Checking ransomware protection…" |
| `recovery` | 80–90 | 3 s | "Checking recovery options…" |
| `engine` | 90–99 | 2 s | "Building your report…" |
| `done` | 100 | — | — |

Inside a band: `pct = start + (end − start) × (1 − e^(−t / expected))`, capped at `end − 1`. It approaches the end of the band but never reaches it until the next marker arrives.

```ts
// desktop/src/renderer/src/lib/progress.ts
export const BANDS = {
  starting: [0, 4, 1000], host: [4, 8, 1000], backup: [8, 28, 4000], patch: [28, 40, 2000],
  software: [40, 55, 2000], protection: [55, 80, 5000], recovery: [80, 90, 3000], engine: [90, 99, 2000],
} as const;
export function progressPct(phase: keyof typeof BANDS | "done", msInPhase: number): number {
  if (phase === "done") return 100;
  const [s, e, exp] = BANDS[phase];
  return Math.min(e - 1, s + (e - s) * (1 - Math.exp(-msInPhase / exp)));
}
```

`ScanningScreen` ticks a `requestAnimationFrame` loop that recomputes `progressPct` with the time since the last phase event. Never show a fake "100%" before `done`.

### 4.9 Screens

`App.tsx` is a 4-state machine; no router.

```
           ┌─────────────┐  valid   ┌────────────┐  ok    ┌───────────┐
 launch ──▶│  License    │────────▶│  Scanning  │──────▶│  Results  │──"Scan again"──▶ Scanning
           └─────────────┘         └────────────┘       └───────────┘
             ▲ invalid ↺               │ error / cancel / timeout
             └─ (already valid → skip) ▼
                                   ┌──────────┐ "Try again" ──▶ Scanning
                                   │  Error   │
                                   └──────────┘
```

#### 4.9.1 License screen [MVP]

1. On mount, call `getLicense()`. If `valid`, skip to the Results-empty state with a "Start scan" button.
2. Show: app name, one-line promise ("A 1-minute, read-only check of this PC's ransomware readiness"), a single `Input` (monospace, paste-friendly), a primary `Button` "Activate".
3. On submit, call `submitLicense(token)`; show a spinner on the button.
4. On `invalid`, show an `Alert` with the message from §3.11's behaviour table, matched by `reason`.
5. Below the input: "Your data stays on this PC. Nothing is uploaded." (POPIA promise, §0.5).

#### 4.9.2 Scanning screen [MVP]

1. Show `Progress` driven by §4.8, the phase message, and elapsed seconds.
2. Show the read-only promise: "We only read settings. Nothing on your PC is changed."
3. If `appInfo().isAdmin` is false, show `AdminHint`: "Tip: for a complete check, close this app, right-click it and choose *Run as administrator*." (The scan still runs.)
4. Show a secondary `Button` "Cancel" → `cancelScan()` → Error screen with "Scan cancelled".

#### 4.9.3 Results screen [MVP]

Layout top to bottom:

| Area | Content | Source in `report.json` (§0.8) |
|---|---|---|
| Header | Large `StatusBadge` for overall, `summary` sentence, "Checked on {generated_at}" | `overall`, `summary`, `generated_at` |
| Top 3 fixes | `FixList` — numbered cards: title, why, steps, "~{effort} min", admin icon if `needs_admin` | `top_fixes` → `fixes[]` |
| Categories | 5 × `CategoryCard` in the fixed order of `categories[]` | `categories[]` |
| Actions | "Open one-page action plan (PDF)", "Open full report", "Scan again" | `pdfAvailable` |
| Footer | `lic` / `org`, engine and baseline version, "Scanned without admin rights" note if `scan.is_admin` false | license state, `engine_version`, `baseline_version`, `scan` |

`CategoryCard`: title + `StatusBadge`; `explanation` paragraph; `EvidenceTable` (label | value | small status dot); "How to fix" links scroll to the matching fix if its id is in `top_fixes`, otherwise expand the fix inline.

`StatusBadge` — the single place status is drawn:

| Status | Colour token | Icon (lucide) | Text |
|---|---|---|---|
| `red` | `rag-red` | `ShieldAlert` | "Act now" |
| `amber` | `rag-amber` | `AlertTriangle` | "Improve" |
| `green` | `rag-green` | `ShieldCheck` | "Good" |
| `unavailable` | `rag-grey` | `CircleSlash` | "Not checked" |
| `failed` | `rag-grey` + dashed border | `CircleX` | "Check failed" |

Status is always shown with **icon + text + colour** — never colour alone (colour-blind users, greyscale printing).

Validation: the renderer parses `ScanResult.report` with `reportSchema` (zod). If parsing fails → Error screen "The report couldn't be read." This catches contract drift during integration instantly.

#### 4.9.4 Error screen [MVP]

One plain sentence from `ScanResult.message`, a "Try again" button, and a small "Details saved to a log file" note. No stack traces.

#### 4.9.5 [STRETCH]

- "Restart as administrator" button (relaunch via `ShellExecute runas`).
- Dark mode.
- Copy-summary-to-clipboard for emailing an IT contractor.

### 4.10 HTML report template

File: `engine/antigravity_engine/templates/report.html.j2` (§2.1). Rendered by the engine from the report model only (§2.3). Opened from the app with `shell.openPath` (default browser), so it must be **fully self-contained**.

Rules:

| Rule | Why |
|---|---|
| One file, inline `<style>`, no `<script>`, no external fonts/images/CDN | Works offline, opens anywhere, can be emailed |
| Jinja `autoescape=True` (set in `render/html.py`) | Software names and versions come from the registry — any `<script>` in a `DisplayName` must render as text |
| Same hex values as §4.3 tokens | HTML, app and PDF look identical |
| Icon + text + colour for every status (Unicode symbols: ● ▲ ✓ ⊘ ✕) | No icon font needed |
| `@media print` rules: A4, no backgrounds required, `page-break-inside: avoid` on category sections | Owners will print it |
| Width max 860 px, readable at 100% zoom on a laptop | — |

Structure:

```
<header>      Product name · overall badge · summary · date · licence org
<section id="actions">   "Your top 3 fixes" (numbered, from top_fixes)
<section id="overview">  5-tile strip: category title + badge (anchor links)
<section class="category" id="{{ c.id }}">   × 5, fixed order
    <h2> title + badge
    <p>  explanation
    <table class="evidence">  label | value | status symbol
    <div class="fixes">       every fix in c.fix_ids (title, why, steps)
<footer>      "Generated locally on this PC. Nothing was uploaded." · engine/baseline versions ·
              "This is a guidance check, not a full security audit."
```

Evidence rendering rules:

| Evidence `status` | Row style |
|---|---|
| red / amber / green | Coloured symbol in third column, normal text |
| `unavailable` | Grey italic value (e.g. "Not checked — needs admin") |
| `failed` | Grey italic value prefixed "Couldn't read:" |
| missing `status` on a row | Treat as neutral, no symbol |

### 4.11 PDF one-pager

**Default: ReportLab (canvas API) inside the engine, `render/pdf.py`** — already pinned in §1.10.

| Option | Verdict | Why |
|---|---|---|
| **ReportLab canvas in engine** | ✅ | Pure-Python wheels (no GTK), deterministic layout, absolute positioning guarantees exactly one page, and the engine CLI produces the PDF standalone — so the PDF can be tested without Electron (§0.2) |
| Electron `webContents.printToPDF` of the HTML | ❌ (fallback only) | Needs a hidden window in main; ties PDF output to Brick D's wiring; Chromium pagination can spill to page 2 |
| WeasyPrint | ❌ | Needs GTK/Pango DLLs on Windows — packaging pain |
| React-PDF (`@react-pdf/renderer`) | ❌ | Extra dependency in the app; same isolation problem as printToPDF |

Fallback if ReportLab layout runs late (decide at 06:00 Day 2): main calls `printToPDF` on `report.html` with `pageSize: 'A4'` and a print stylesheet that hides everything except header + top fixes. Keep this as a 20-line function ready in a branch, not merged.

**Top-3 selection:** done by the engine (§0.8 ranking rule, implemented in §2.6). The PDF and app only render `top_fixes` in order — they never re-rank.

**Layout spec (A4 portrait, 210 × 297 mm, 15 mm margins)** — Frank writes the spec and copy, Tshedi implements:

| Block | Position (from top) | Content | Overflow rule |
|---|---|---|---|
| Header | 15–40 mm | "Antigravity — Cyber Health Action Plan", org, date, overall badge (coloured box + word) | Org truncated to 40 chars |
| Summary | 42–55 mm | `summary` sentence | 2 lines max |
| Category strip | 58–75 mm | 5 equal boxes: title + status word + symbol | Fixed |
| Fix 1–3 | 80–255 mm, 3 × ~55 mm boxes | Rank number, `title` (bold 13 pt), `why` (10 pt), up to 4 `steps` (10 pt), "~N min · Needs admin" | Steps > 4 → show 4 + "…see full report"; each line truncated with "…" at box width |
| No fixes case | same area | "Nothing urgent. Re-check monthly." | — |
| Footer | 265–282 mm | "Generated locally — nothing was uploaded. Guidance only, not a full audit." · versions | Fixed |

Fonts: ReportLab built-in Helvetica (no font files to bundle). Colours: §4.3 hex values. Test in `engine/tests/test_render.py`: PDF exists, starts with `%PDF`, and for the all-states mock the canvas reports exactly one `showPage()` call.

### 4.12 Mock data for UI development

Frank develops the whole UI before Bricks A and B exist, in two ways:

**1. Component tests** import `/shared/fixtures/report.*.json` (§2.11 step 5) plus this hand-written file that exercises every status at once.

`desktop/src/renderer/src/mocks/report.all-states.json`:

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-11-14T17-02-44Z_beef",
  "generated_at": "2026-11-14T17:02:46Z",
  "engine_version": "0.1.0",
  "baseline_version": "2026-11-01",
  "overall": "red",
  "summary": "2 urgent issues need attention this week. Some checks couldn't run.",
  "categories": [
    {
      "id": "backup", "title": "Backup evidence", "status": "green",
      "explanation": "File History backed up this PC yesterday.",
      "evidence": [
        { "label": "File History", "value": "Last backup 13 Nov 2026", "status": "green" },
        { "label": "OneDrive folders", "value": "Desktop, Documents", "status": "green" },
        { "label": "Shadow copies", "value": "Not checked — needs admin", "status": "unavailable" }
      ],
      "fix_ids": []
    },
    {
      "id": "patch", "title": "Windows updates", "status": "amber",
      "explanation": "The newest update was installed 55 days ago, and a restart is waiting to finish updates.",
      "evidence": [
        { "label": "Latest update", "value": "KB5043064 on 20 Sep 2026", "status": "amber" },
        { "label": "Restart needed", "value": "Yes", "status": "amber" }
      ],
      "fix_ids": ["install-updates"]
    },
    {
      "id": "software", "title": "Outdated software", "status": "red",
      "explanation": "Google Chrome is out of date and has known security holes.",
      "evidence": [
        { "label": "Google Chrome", "value": "118.0.5993.118 (needs 131 or newer)", "status": "red" },
        { "label": "Other apps", "value": "42 apps not on our watch list" }
      ],
      "fix_ids": ["update-outdated-apps"]
    },
    {
      "id": "protection", "title": "Ransomware protections", "status": "red",
      "explanation": "Microsoft Defender antivirus is switched off, so nothing is scanning for ransomware.",
      "evidence": [
        { "label": "Defender antivirus", "value": "Off", "status": "red" },
        { "label": "Controlled Folder Access", "value": "Disabled", "status": "amber" },
        { "label": "BitLocker (C:)", "value": "Not checked — needs admin", "status": "unavailable" },
        { "label": "ASR rules", "value": "Couldn't read: settings unavailable", "status": "failed" }
      ],
      "fix_ids": ["enable-defender", "enable-cfa"]
    },
    {
      "id": "recovery", "title": "Recovery readiness", "status": "failed",
      "explanation": "This check couldn't run on this PC.",
      "evidence": [],
      "fix_ids": []
    }
  ],
  "fixes": [
    { "id": "enable-defender", "category": "protection", "severity": "red",
      "title": "Turn Microsoft Defender back on",
      "why": "Without antivirus, ransomware can run unnoticed.",
      "steps": ["Open Start and search for Windows Security", "Go to Virus & threat protection", "Under settings, choose Manage settings", "Switch Real-time protection On"],
      "effort_minutes": 5, "needs_admin": true },
    { "id": "update-outdated-apps", "category": "software", "severity": "red",
      "title": "Update Google Chrome",
      "why": "Old browsers are a common way attackers get in.",
      "steps": ["Open Chrome → Settings → About Chrome", "Wait for the update, then click Relaunch"],
      "effort_minutes": 5, "needs_admin": false },
    { "id": "install-updates", "category": "patch", "severity": "amber",
      "title": "Install Windows updates and restart",
      "why": "Updates close the holes ransomware uses to get in.",
      "steps": ["Open Settings → Windows Update", "Click Check for updates", "Restart when asked"],
      "effort_minutes": 30, "needs_admin": true },
    { "id": "enable-cfa", "category": "protection", "severity": "amber",
      "title": "Turn on Controlled Folder Access",
      "why": "It stops unknown apps from changing your documents.",
      "steps": ["Open Windows Security → Virus & threat protection", "Choose Manage ransomware protection", "Switch Controlled folder access On"],
      "effort_minutes": 5, "needs_admin": true }
  ],
  "top_fixes": ["enable-defender", "update-outdated-apps", "install-updates"],
  "scan": { "is_admin": false, "duration_ms": 6230, "os_caption": "Microsoft Windows 10 Pro" }
}
```

**2. Mock mode in the running app.** When `AG_MOCK=1`, `main/mock.ts` replaces `runCollector`/`runEngine`: it emits the §4.8 phase events on a realistic 10-second timer, then returns `report.all-states.json` (or the fixture named by `AG_MOCK_FIXTURE`). License checks still run for real.

1. ```powershell
   # cwd: antigravity/desktop
   $env:AG_MOCK = "1"; npm run dev
   ```
2. To try a specific fixture:
   ```powershell
   # cwd: antigravity/desktop
   $env:AG_MOCK = "1"; $env:AG_MOCK_FIXTURE = "report.defender-off.json"; npm run dev
   ```
3. Clear when done:
   ```powershell
   # cwd: antigravity/desktop
   Remove-Item Env:AG_MOCK, Env:AG_MOCK_FIXTURE -ErrorAction SilentlyContinue
   ```

`mock.ts` is excluded from packaged builds: `paths.ts` ignores `AG_MOCK` when `app.isPackaged` is true.

### 4.13 Landing page and Vercel deploy

`/landing` is a separate Vite + React project with its own `package.json` and lockfile (§1.10). It shares no code with `/desktop` — copy any component you want to reuse.

Page sections [MVP]:

| Section | Content |
|---|---|
| Hero | One-line promise, screenshot of the Results screen, "Download for Windows" button |
| How it works | 3 steps: enter key → 1-minute read-only scan → action plan |
| The 5 checks | One line each, plain English |
| Privacy | "Runs on your PC. Reads settings only. Uploads nothing." (POPIA-minimal) |
| Get a demo key | Instructions to request one from the team at the stand |
| Footer | Team names, HackSecure 2026 Track 3 |

Installer hosting — **Default:** attach the installer to a **GitHub Release** and link to it from the landing page. Rationale: release assets suit large binaries and need no extra service. If the repo is private, release downloads need a login — either make the repo public before pitches or host the installer on a team Google Drive link. Never commit the installer into `landing/public`.

Deploy steps (do the first deploy **at home**, before the event):

1. Push `landing/` to `main`.
2. Open vercel.com → **Add New… → Project** → import the GitHub repo.
3. Set **Root Directory** to `landing`.
4. Confirm **Framework Preset** = Vite, **Build Command** = `npm run build`, **Output Directory** = `dist`, **Install Command** = `npm ci`.
5. Under **Settings → General → Node.js Version**, pick 22.x (matches §1.1).
6. Click **Deploy**. Note the `*.vercel.app` URL in `docs/demo-script.md`.
7. Add `landing/vercel.json`:
   ```json
   { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
   ```
   (Only needed if you add client-side routes; harmless otherwise.)
8. From then on, every push to `main` that touches `landing/` redeploys automatically. At the venue, a `git push` over phone hotspot is enough.
9. Before 11:30 Day 2, update the download button to the final GitHub Release URL (§5.8 step 9) and push.

Local check:

```powershell
# cwd: antigravity/landing
npm ci --prefer-offline; npm run build; npm run preview
```

### 4.14 Brick C is done when…

**Phase 1 — mocked (no other brick needed)**
- [ ] `npm run typecheck` and `npm run test` pass.
- [ ] `fixtures.test.tsx` renders `report.all-states.json` and every `/shared/fixtures/report.*.json`: 5 cards, correct badge text for every status, ≤ 3 fixes in `FixList`, "Not checked" and "Check failed" visible.
- [ ] `progress.test.ts`: bar never decreases, never hits 100 before `done`, stays inside each band.
- [ ] `AG_MOCK=1` run goes License → Scanning → Results → "Scan again" without errors in DevTools console.
- [ ] Zod rejects a report with a missing category (test).
- [ ] Every screen readable at 1366 × 768 (typical SMME laptop).

**Phase 2 — real bricks**
- [ ] With Brick B's collector and Brick A's engine on `main`, a real scan (no `AG_MOCK`) on Dev-1 and Dev-2 shows results in < 60 s.
- [ ] Non-admin run shows the admin hint and grey "Not checked" rows.
- [ ] "Open PDF" and "Open full report" open the right files; PDF is one page.
- [ ] HTML report opened offline looks identical to the app's colours; a test app named `<script>alert(1)</script>` (mock fixture) renders as text.

**Landing**
- [ ] Deployed on Vercel; download link works from a phone on mobile data.

**Demo**
- [ ] `docs/demo-script.md` rehearsed twice end to end, under 3 minutes.

---

## §5 Brick D: Packaging & Deployment (Schwan)

Schwan turns three independent bricks into one Windows installer and proves it works on a machine that has never seen our code. He also owns the main-process wiring (paths, run folders, spawning — §4.5–4.7).

### 5.1 Folder layout

```
installer/
├── build-all.ps1               ✚ content §5.8 — builds everything in order
├── smoke-test.ps1                checks an installed app (§5.9)
├── checksums.ps1                 SHA-256 of the installer
├── installer.nsh                 NSIS custom include (§5.3)
└── stubs/                    ✚   for Brick D's isolation test (§5.10)
    ├── collector-stub.ps1        prints AG-PHASE lines, copies a fixture to -OutputPath
    └── README.md                 how to point paths.ts at the stubs
desktop/
├── electron-builder.yml          §5.2
├── release/                      (git-ignored) build output
└── src/main/
    ├── index.ts                  §5.6
    ├── ipc.ts                    §4.6
    ├── paths.ts                  §5.5
    └── runs.ts                   §5.6 step 8
```

Add `desktop/release/` and `engine/build/` to `.gitignore` (§1.7).

### 5.2 electron-builder.yml, field by field

```yaml
# desktop/electron-builder.yml
appId: com.teamantigravity.cyberhealth
productName: Antigravity
copyright: "© 2026 Team Antigravity"
artifactName: "Antigravity-Setup-${version}.${ext}"

directories:
  output: release
  buildResources: resources

files:
  - "out/**"
  - "package.json"
  - "!**/*.map"

asar: true

extraResources:
  - from: "../engine/dist/engine"
    to: "engine"
    filter: ["**/*"]
  - from: "../collector"
    to: "collector"
    filter:
      - "**/*.ps1"
      - "!tests/**"
      - "!mocks/**"
  - from: "../baseline/software-baseline.json"
    to: "baseline/software-baseline.json"

win:
  target:
    - target: nsis
      arch: [x64]
  icon: resources/icon.ico
  requestedExecutionLevel: asInvoker
  forceCodeSigning: false

nsis:
  oneClick: false
  perMachine: false
  allowElevation: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: always
  createStartMenuShortcut: true
  shortcutName: Antigravity
  runAfterFinish: true
  deleteAppDataOnUninstall: true
  include: ../installer/installer.nsh
  installerIcon: resources/icon.ico
  uninstallerIcon: resources/icon.ico
  uninstallDisplayName: "Antigravity Cyber Health Check"

compression: normal
publish: null
npmRebuild: false
```

| Field | Value | Why |
|---|---|---|
| `appId` | `com.teamantigravity.cyberhealth` | Stable Windows identity (taskbar grouping, uninstall key). Never change after first build |
| `productName` | `Antigravity` | Name in Start menu, install folder and window title |
| `artifactName` | `Antigravity-Setup-${version}.${ext}` | Predictable filename for checksums and the landing link |
| `directories.output` | `release` | Where installers land (git-ignored) |
| `directories.buildResources` | `resources` | Icon and installer assets |
| `files` | `out/**`, `package.json`, no source maps | Only electron-vite's build output goes into the asar |
| `asar` | `true` | Packs app JS into one archive; faster install. Engine and collector stay **outside** (extraResources) because executables and scripts can't run from inside an asar |
| `extraResources[engine]` | `engine/dist/engine` → `resources/engine` | The PyInstaller one-folder build (§2.12) |
| `extraResources[collector]` | `*.ps1` only, minus `tests/` and `mocks/` | Mocks in a shipped product would be an attack surface (§3.12) |
| `extraResources[baseline]` | one JSON file | Engine reads it via `--baseline` (§2.8) |
| `win.target` | `nsis`, `x64` | Standard installer; SMME PCs are 64-bit |
| `win.requestedExecutionLevel` | `asInvoker` | App opens without a UAC prompt; users can still choose Run as administrator for a full check (§4.9.2). **Default** for MVP — a UAC prompt on launch is a worse first impression than some grey rows |
| `win.forceCodeSigning` | `false` | We ship unsigned for the demo (§5.7) |
| `compression` | `normal` | `maximum` saves little and adds minutes per build at 03:00 |
| `publish` | `null` | Never auto-upload; releases are manual (§5.8 step 9) |
| `npmRebuild` | `false` | We have no native Node modules; skips a step that would need network/build tools |

### 5.3 NSIS installer settings

| Setting | Value | Why |
|---|---|---|
| `oneClick` | `false` | Shows a normal wizard — feels trustworthy to a non-technical owner |
| `perMachine` | `false` | Installs to `%LOCALAPPDATA%\Programs\Antigravity` with **no admin rights needed**. Works on locked-down PCs |
| `allowElevation` | `false` | Stays per-user; no UAC during install |
| `allowToChangeInstallationDirectory` | `true` | Standard expectation in a wizard |
| `createDesktopShortcut` | `always` | Owners find it again |
| `runAfterFinish` | `true` | Goes straight to the license screen |
| `deleteAppDataOnUninstall` | `true` | Removes `%APPDATA%\Antigravity` (license, settings). POPIA-minimal: uninstall leaves nothing |
| `include` | `../installer/installer.nsh` | Removes our second data folder (below) |

`installer/installer.nsh` — removes scan runs and logs under `%LOCALAPPDATA%\Antigravity`, which `deleteAppDataOnUninstall` doesn't cover:

```nsis
; installer/installer.nsh
!macro customUnInstall
  ${ifNot} ${isUpdated}
    RMDir /r "$LOCALAPPDATA\Antigravity"
  ${endIf}
!macroend
```

`${isUpdated}` skips deletion when the uninstaller runs as part of an upgrade.

### 5.4 Bundling the engine and collector as extraResources

Installed layout (per-user install):

```
%LOCALAPPDATA%\Programs\Antigravity\
├── Antigravity.exe
├── resources\
│   ├── app.asar                       main, preload, renderer
│   ├── engine\
│   │   ├── engine.exe                 PyInstaller one-folder (§2.12)
│   │   └── _internal\                 Python runtime, templates, schemas
│   ├── collector\
│   │   ├── collector.ps1
│   │   ├── lib\Common.ps1, Allowlist.ps1
│   │   └── probes\*.ps1
│   └── baseline\software-baseline.json
└── (Electron runtime files)

%APPDATA%\Antigravity\                  Electron userData
└── license.txt

%LOCALAPPDATA%\Antigravity\
├── runs\<run_id>\scan.json, report.json, report.html, action-plan.pdf
└── logs\last-error.txt
```

The public key for license checks is compiled into the main bundle (`?raw` import, §3.11), so it's not a separate resource.

### 5.5 Path resolution: dev vs packaged

```ts
// desktop/src/main/paths.ts
import { app } from "electron";
import path from "node:path";

const repoRoot = () => path.resolve(app.getAppPath(), "..");          // dev: …\antigravity
const res = (...p: string[]) => path.join(process.resourcesPath, ...p);

export const paths = {
  collectorScript: () =>
    app.isPackaged ? res("collector", "collector.ps1")
                   : path.join(repoRoot(), "collector", "collector.ps1"),

  baseline: () =>
    app.isPackaged ? res("baseline", "software-baseline.json")
                   : path.join(repoRoot(), "baseline", "software-baseline.json"),

  engine: () => {
    if (app.isPackaged) {
      const dir = res("engine");
      return { cmd: path.join(dir, "engine.exe"), prefixArgs: [] as string[], cwd: dir };
    }
    if (process.env.AG_ENGINE_EXE === "1") {                         // dev, but test the built exe
      const dir = path.join(repoRoot(), "engine", "dist", "engine");
      return { cmd: path.join(dir, "engine.exe"), prefixArgs: [], cwd: dir };
    }
    const dir = path.join(repoRoot(), "engine");                     // dev default: run from source
    return { cmd: path.join(dir, ".venv", "Scripts", "python.exe"),
             prefixArgs: ["-m", "antigravity_engine"], cwd: dir };
  },

  runsRoot: () => path.join(process.env.LOCALAPPDATA ?? app.getPath("userData"), "Antigravity", "runs"),
  logsRoot: () => path.join(process.env.LOCALAPPDATA ?? app.getPath("userData"), "Antigravity", "logs"),
  licenseFile: () => path.join(app.getPath("userData"), "license.txt"),
  mockEnabled: () => !app.isPackaged && process.env.AG_MOCK === "1",
};
```

| Resource | Dev (`npm run dev`) | Packaged |
|---|---|---|
| Collector | `<repo>\collector\collector.ps1` | `resources\collector\collector.ps1` |
| Engine | `<repo>\engine\.venv\Scripts\python.exe -m antigravity_engine` (or built exe with `AG_ENGINE_EXE=1`) | `resources\engine\engine.exe` |
| Baseline | `<repo>\baseline\software-baseline.json` | `resources\baseline\software-baseline.json` |
| Runs/logs | `%LOCALAPPDATA%\Antigravity\…` | same |
| Mock mode | allowed | always off |

`app.getAppPath()` in dev is `<repo>\desktop`, hence `repoRoot()` = one level up. Check once with a `console.log` on Day 1 — this is the most common "works in dev, breaks packaged" bug.

### 5.6 Startup sequence

| # | Step | Who | Files touched | On failure |
|---|---|---|---|---|
| 1 | User double-clicks the shortcut; `Antigravity.exe` starts | — | `Antigravity.exe`, `resources\app.asar` | — |
| 2 | Main: `app.requestSingleInstanceLock()`; quit if another copy runs | D | — | Focus existing window |
| 3 | Main: create `BrowserWindow` with §4.4 security flags; register IPC handlers (§4.6) | D | `out/main/index.js`, `out/preload/index.js` | — |
| 4 | Renderer loads; calls `getLicense()` | C | `out/renderer/index.html` | — |
| 5 | Main reads `license.txt` and runs `verifyLicense()` | B | `%APPDATA%\Antigravity\license.txt` | Missing/invalid → License screen |
| 6 | User enters a key → `submitLicense()` → verify → on success write `license.txt` | B | `license.txt` (write) | Error message (§3.11) |
| 7 | User clicks "Start scan" → `scan:run`; main re-verifies the license | B, D | `license.txt` | `stage: "license"` → License screen |
| 8 | Main creates the run folder: generate `runId`, `mkdir runs\<runId>`, delete older run folders (keep latest only — scan history is cut, POPIA-minimal) | D | `%LOCALAPPDATA%\Antigravity\runs\` | `stage: "collector"`, "Couldn't prepare a folder" |
| 9 | Main spawns the collector (§4.7); forwards `AG-PHASE:` lines as `scan:progress` | D → B | `resources\collector\*.ps1` (read), `runs\<runId>\scan.json` (written by collector) | Exit ≠ 0, timeout 45 s, or missing `scan.json` → Error screen |
| 10 | Main spawns the engine (§4.7); sends `phase: "engine"` | D → A | `resources\engine\engine.exe`, `resources\baseline\software-baseline.json`, `scan.json` (read); `report.json`, `report.html`, `action-plan.pdf` (written) | Exit 1/timeout 15 s → Error screen; exit 3 → continue with `pdfAvailable: false` |
| 11 | Main reads `report.json` (≤ 2 MB), sends `phase: "done"`, resolves `ScanResult` | D | `report.json` | Unreadable → Error screen |
| 12 | Renderer validates with zod, shows Results | C | — | Zod failure → Error screen |
| 13 | User clicks "Open PDF" / "Open full report" → main `shell.openPath(...)` | D | `action-plan.pdf` / `report.html` | Show "No PDF viewer found" if `openPath` returns an error string |

Every failure writes the technical detail (exit code, first 4 KB of stderr) to `logs\last-error.txt`, overwriting the previous one.

### 5.7 Code signing and SmartScreen

**We ship the demo unsigned. This is acceptable for the hackathon.** A trusted code-signing certificate takes days to issue and costs money; that's out of scope for two days. Say so plainly if judges ask, and list "signed installer" as a next step in the pitch.

What unsigned means in practice:

| Where | What happens | Handling |
|---|---|---|
| Installer downloaded in a browser | File gets "Mark of the Web" → SmartScreen shows **"Windows protected your PC"** | Click **More info** → **Run anyway** |
| Installer copied from USB | Usually no Mark of the Web → no SmartScreen prompt | Preferred for the demo laptop |
| Browser download warning (Edge/Chrome) | May say the file "isn't commonly downloaded" | **⋯ → Keep → Keep anyway** |
| Windows Properties | Downloaded file shows an "Unblock" checkbox | Tick **Unblock** → OK, then run — avoids SmartScreen |
| Defender | Should not flag us; verified in §5.9 with real-time protection on | If it does: report the false positive at the Microsoft submission portal after the event; for the demo, use the pre-installed laptop |

Demo plan:

1. Install the final build on the demo laptop **before** the 11:00 mentor checkpoint, from USB.
2. Pin the app to the taskbar; run one scan so Windows has seen the app.
3. If the pitch includes installing live, rehearse the SmartScreen clicks twice and narrate them: "Unsigned for the hackathon — signing is step one after today."
4. Have a 30-second screen recording of a full scan as a backup if the laptop misbehaves.

### 5.8 Building the installer

`installer/build-all.ps1` builds everything in dependency order and stops at the first failure:

```powershell
# installer/build-all.ps1   — run from repo root
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

Write-Host '0/7 Contract check';    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\contract-check.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '1/7 Engine tests';      & "$root\engine\.venv\Scripts\python.exe" -m pytest -q "$root\engine\tests"; if ($LASTEXITCODE) { exit 1 }
Write-Host '2/7 Engine exe';        Push-Location "$root\engine"; & .venv\Scripts\pyinstaller.exe engine.spec --clean --noconfirm; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '3/7 Resource manifest'; Push-Location "$root\desktop"; node ..\installer\make-manifest.mjs; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '4/7 Collector tests';   & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-ReadOnly.ps1"; if ($LASTEXITCODE) { exit 1 }
                                    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-Collector.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '5/7 Desktop install';   Push-Location "$root\desktop"; npm ci --prefer-offline; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '6/7 Desktop tests';     Push-Location "$root\desktop"; npm run typecheck; if ($LASTEXITCODE) { Pop-Location; exit 1 }; npm run test; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '7/7 Installer';         Push-Location "$root\desktop"; npm run dist; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
& "$PSScriptRoot\checksums.ps1"
Write-Host "DONE -> desktop\release" -ForegroundColor Green
```

Step 0 runs `installer/contract-check.ps1` (collector `-DryRun` → `engine/tools/validate.py scan` → engine `--json-only` → `validate.py report`; prints `CONTRACT OK`), so no installer is ever built across a broken contract (§6.3). Step 3 runs `installer/make-manifest.mjs`, which writes SHA-256 hashes of the shipped collector, engine and baseline files to `desktop/src/main/resource-hashes.json`; `desktop/src/main/integrity.ts` checks them before every scan in packaged mode (§7.8).

`installer/checksums.ps1`:

```powershell
# installer/checksums.ps1
$exe = Get-ChildItem (Join-Path $PSScriptRoot '..\desktop\release\Antigravity-Setup-*.exe') | Select-Object -First 1
$hash = (Get-FileHash $exe.FullName -Algorithm SHA256).Hash
"$hash  $($exe.Name)" | Set-Content (Join-Path $exe.DirectoryName 'SHA256SUMS.txt') -Encoding ascii
Write-Host $hash
```

Steps:

1. Check out the commit to build:
   ```powershell
   # cwd: antigravity
   git checkout main; git pull
   ```
2. Confirm caches are warm (§1.6): `dir $env:LOCALAPPDATA\electron\Cache` lists the Electron 34 zip and `dir $env:LOCALAPPDATA\electron-builder\Cache` lists `nsis` and `winCodeSign`.
3. Run the full build:
   ```powershell
   # cwd: antigravity
   powershell -NoProfile -ExecutionPolicy Bypass -File installer\build-all.ps1
   ```
4. For a quick packaging check without NSIS (≈ 1 min):
   ```powershell
   # cwd: antigravity/desktop
   npm run dist:dir
   .\release\win-unpacked\Antigravity.exe
   ```
5. Find the output: `desktop\release\Antigravity-Setup-0.1.0.exe` and `SHA256SUMS.txt`.
6. Expected installer size: ~100–150 MB (Electron + Python runtime). Much smaller means the engine folder is missing; check `release\win-unpacked\resources\engine\engine.exe` exists.
7. Run the clean-VM test (§5.9).
8. For release candidates: bump `version` in `desktop/package.json` to `1.0.0` for RC1 (Day 2 06:45) and follow the release-candidate rule in §8.7. Tag `v1.0.0-demo` at 11:20 on whichever RC is submitted — do **not** start a fresh build at 11:00.
9. Create a GitHub Release from the tag, attach the installer and `SHA256SUMS.txt`, and give Frank the URL for the landing page (§4.13 step 9). Done by **11:25**, so submission happens by 11:30 (§8.6).

### 5.9 Clean-Windows-VM test

Run on Schwan's Hyper-V VM (§1.2 step 13), reverted to the `clean-baseline` checkpoint every time. The VM has no Python, Node or Git, Defender on with real-time protection, and a standard (non-admin) user account plus the admin account.

| # | Step | Expected result |
|---|---|---|
| 1 | In Hyper-V Manager, apply checkpoint `clean-baseline`; start the VM | VM boots to the desktop |
| 2 | Disconnect the VM's network adapter (Settings → Network Adapter → Not connected) | No network — proves offline operation |
| 3 | Copy `Antigravity-Setup-x.y.z.exe` and `SHA256SUMS.txt` into the VM (Enhanced Session clipboard or a shared VHD) | Files on the VM desktop |
| 4 | In the VM, run `Get-FileHash .\Antigravity-Setup-*.exe -Algorithm SHA256` (cwd: Desktop) | Hash matches `SHA256SUMS.txt` |
| 5 | Log in as the **standard user**; double-click the installer | Wizard appears; no UAC prompt. SmartScreen may appear → More info → Run anyway (§5.7) |
| 6 | Accept defaults; finish with "Run Antigravity" ticked | App opens on the License screen within 5 s; desktop + Start menu shortcuts exist |
| 7 | Enter an invalid key `AG1.xxx.yyy` | "That doesn't look like an Antigravity key…" |
| 8 | Enter the expired test token (§3.11 step 5) | "This key expired on …" |
| 9 | Enter demo key `AG-DEMO-0001` token | Main screen with "Start scan"; footer shows licence id |
| 10 | Click "Start scan"; time it | Progress moves through all phase messages; Results appear in **< 60 s**; admin hint shown |
| 11 | Check the Results | 5 categories; admin-only items show "Not checked"; top fixes listed |
| 12 | Click "Open one-page action plan (PDF)" | PDF opens in Edge; exactly one page |
| 13 | Click "Open full report" | HTML opens in Edge, offline, colours correct |
| 14 | Check Windows Security → Protection history | No detections of Antigravity, PowerShell or engine.exe |
| 15 | Close the app; right-click the shortcut → Run as administrator (admin credentials); scan again | More rows rated (BitLocker, restore points, shadow copies); still < 60 s |
| 16 | Close and reopen the app | Goes straight past the License screen (license remembered) |
| 17 | In `%LOCALAPPDATA%\Antigravity\runs` | Exactly one run folder (older run deleted) |
| 18 | Open `scan.json` and search for the VM's username and computer name | Neither appears (POPIA) |
| 19 | Settings → Apps → Installed apps → Antigravity → Uninstall | Uninstaller completes without UAC |
| 20 | Check `%LOCALAPPDATA%\Programs\Antigravity`, `%APPDATA%\Antigravity`, `%LOCALAPPDATA%\Antigravity` and the shortcuts | All gone |
| 21 | Apply checkpoint `clean-baseline` again | VM ready for the next build |

Record each run in `docs/decisions.md` as one line: date/time, build version, pass/fail, step number of any failure.

`installer/smoke-test.ps1` automates steps 6, 17 and 20 checks (existence of install folder, shortcuts, run folder count, cleanup after uninstall); run it inside the VM from the copied repo `installer` folder:

```powershell
# cwd: (in VM) Desktop\installer
powershell -NoProfile -ExecutionPolicy Bypass -File .\smoke-test.ps1 -Phase AfterInstall
powershell -NoProfile -ExecutionPolicy Bypass -File .\smoke-test.ps1 -Phase AfterUninstall
```

### 5.10 Brick D is done when…

Schwan's Day 1 16:00–18:00 deliverable is this isolation set: the main-process pipeline (paths, spawn, IPC) working with stubs (§8.1 C3). NSIS packaging follows at 21:15.

**Isolation (no real engine or real report needed)**
- [ ] With `installer/stubs/collector-stub.ps1` swapped in for the collector and a stub engine folder containing a copied `report.json`, `npm run dist:dir` produces an app that completes the full startup sequence (§5.6) — proves wiring, paths and spawning independent of Bricks A and B.
- [ ] `paths.ts` resolves correctly in dev and in `release\win-unpacked` (log check, §5.5).
- [ ] Kill-tree works: cancelling a scan leaves no `powershell.exe` or `engine.exe` in Task Manager.

**Integrated**
- [ ] `build-all.ps1` runs green from a fresh clone with Wi-Fi off (§1.5 caches).
- [ ] Clean-VM test §5.9 passes all 21 steps on Windows 11; steps 1–14 also pass on a Windows 10 VM if one is available.
- [ ] Installer < 200 MB; SHA-256 recorded.
- [ ] Final installer built from tag `v1.0.0-demo`, attached to the GitHub Release, link handed to Frank, all before **11:30 Day 2**.
- [ ] Demo laptop has the final build installed from USB and one successful scan done before **11:00 Day 2**.

---

## §6 Integration sequence

Integration is a single, ordered run-through led by **Tshedi** (merges) with each owner on hand for their brick. Target windows (§8.4): **Day 1 19:00–21:00** for Phases 1–3 and 5 (ending with the `v0.1-integrated` tag), and **21:15–00:00** for Phases 4 and 6 (first installer, `v0.2-installer`). Each step lists **who**, **files**, **action** (with working directory), **expected result** and **rollback**. Do not start a step until the previous one shows its expected result.

### 6.1 Before you start

1. Every owner confirms in the team chat: "my brick's isolation test passes on `brick/<x>` rebased on `main`" (§0.2, §2.13, §3.13, §4.14 Phase 1, §5.10 isolation).
2. Everyone pushes their branch. Nobody pushes to a brick branch again until Phase 1 is finished.
3. Tshedi tags the starting point so any phase can be rolled back cleanly:
   ```powershell
   # cwd: antigravity
   git checkout main; git pull; git tag pre-integration; git push origin pre-integration
   ```
4. Confirm the cross-brick pieces are on the brick branches: collector `-RunId` and `AG-PHASE:` markers (§3.2–§3.3) and `engine/tools/validate.py` (§2.1).

### 6.2 Phase 1 — Merge the four bricks

Order matters: contract first, then producers before consumers.

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 1.1 | Shakir → Tshedi merges | `shared/contract/*`, `shared/fixtures/*` | Merge any open `contract/*` PR in GitHub (squash). Then: `git pull` (cwd: `antigravity`) | `shared/contract/CHANGELOG.md` shows the final `1.x.0`; all four fixtures present | `git revert <merge-sha>`; push |
| 1.2 | Tshedi | `engine/**`, `baseline/**` | Merge `brick/engine` PR. Then `git pull` and `engine\.venv\Scripts\python -m pytest -q` (cwd: `antigravity/engine`) | All tests green on `main` | `git revert <merge-sha>`; fix on `brick/engine` |
| 1.3 | Shakir → Tshedi merges | `collector/**`, `desktop/src/main/license/**`, `tools/issue-license.mjs`, `shared/license/public-key.pem` | Merge `brick/collector`. Then: `powershell -NoProfile -ExecutionPolicy Bypass -File tests\Test-ReadOnly.ps1` and `…\Test-Collector.ps1` (cwd: `antigravity/collector`) | `READ-ONLY OK`; all mock cases pass | `git revert <merge-sha>` |
| 1.4 | Frank → Tshedi merges | `desktop/src/renderer/**`, `desktop/src/shared/ipc.ts`, `desktop/package*.json` | Merge `brick/desktop-ui`. Then `npm ci --prefer-offline; npm run typecheck; npm run test` (cwd: `antigravity/desktop`) | Typecheck clean; vitest green | `git revert <merge-sha>` |
| 1.5 | Schwan → Tshedi merges | `desktop/src/main/**` (except `license/`), `desktop/src/preload/**`, `desktop/electron-builder.yml`, `installer/**` | Merge `brick/packaging`. Resolve any conflict in `desktop/src/main/ipc.ts` in favour of the §4.6 contract. Re-run 1.4's commands | Still green; `npm run dev` opens the window | `git revert <merge-sha>` |
| 1.6 | Frank → Tshedi merges | `landing/**` | Merge `brick/landing` (independent; may go any time) | Vercel auto-deploys from `main` | Revert; Vercel keeps the previous deployment live |
| 1.7 | Tshedi | — | `git tag merged-bricks; git push origin merged-bricks` (cwd: `antigravity`) | Tag on GitHub | — |

### 6.3 Phase 2 — Wire collector → engine

The contract mismatch must fail **loudly** here, not as a blank screen later.

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 2.1 | Tshedi | `engine/tools/validate.py` (§2.1) | Confirm the validator exists and works on a fixture: `.venv\Scripts\python tools\validate.py scan ..\shared\fixtures\scan.healthy.json` (cwd: `antigravity/engine`) | Prints `VALID scan 1.0.0`, exit 0 | — |
| 2.2 | Shakir | `out/int/scan.json` (git-ignored) | Run the real collector on Dev-1, non-elevated: `powershell -NoProfile -ExecutionPolicy Bypass -File collector\collector.ps1 -OutputPath out\int\scan.json -RunId 2026-11-14T21-30-00Z_0001` (cwd: `antigravity`; create `out\int` first with `mkdir out\int`) | Exit 0; `scan.json` exists; `AG-PHASE:` lines printed | Fix collector on a `fix/*` branch; continue Phase 2 with fixtures |
| 2.3 | Shakir | — | **Schema gate:** `engine\.venv\Scripts\python engine\tools\validate.py scan out\int\scan.json` (cwd: `antigravity`) | `VALID`. On failure prints the JSON path and rule, e.g. `INVALID $.patch.hotfixes: {…} is not of type 'array'`, exit 1 | Do not continue. Owner of the wrong side fixes it: if the schema is right → Shakir; if the schema is wrong → §0.10 contract PR |
| 2.4 | Shakir | — | Repeat 2.2–2.3 **elevated** on Dev-1, then non-elevated and elevated on Dev-2 (§3.9) | Four `VALID` results | As 2.3 |
| 2.5 | Tshedi | `out/int/report.json`, `.html`, `.pdf` | Run the engine on the real scan: `engine\.venv\Scripts\python -m antigravity_engine --in out\int\scan.json --out out\int --baseline baseline\software-baseline.json` (cwd: `antigravity`) | Exit 0 (or 3 if PDF render broken); three output files | Exit 2 means the gate in 2.3 was skipped — go back to 2.3 |
| 2.6 | Tshedi | — | Validate the engine output: `engine\.venv\Scripts\python engine\tools\validate.py report out\int\report.json` (cwd: `antigravity`) | `VALID report 1.0.0` | Fix engine on `fix/*` |
| 2.7 | Tshedi + Shakir | — | Read `report.html` side by side with Windows Security on Dev-1. Every status must make sense for that machine | Agreement, or a written list of rule/collector bugs | Log bugs; continue with the fixture-based path |
| 2.8 | Shakir | `installer/contract-check.ps1` (§5.8) | Run the combined gate once: `powershell -NoProfile -ExecutionPolicy Bypass -File installer\contract-check.ps1` (cwd: `antigravity`) | Runs collector `-DryRun` → validate scan → engine `--json-only` → validate report; prints `CONTRACT OK` | — |

`contract-check.ps1` becomes step 0 of `build-all.ps1` (§5.8), so no installer is ever built across a broken contract.

### 6.4 Phase 3 — Wire engine → UI

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 3.1 | Frank | `shared/fixtures/report.*.json` | Regenerate UI fixtures from the merged engine (§2.11 step 5), then `npm run test` (cwd: `antigravity/desktop`) | Tests still green against freshly generated reports | If tests fail, it's contract drift: compare `reportSchema.ts` (zod) with `report.schema.json`; fix whichever is wrong |
| 3.2 | Frank | — | Load the **real** `out\int\report.json` in mock mode: `$env:AG_MOCK="1"; $env:AG_MOCK_FIXTURE="..\..\out\int\report.json"; npm run dev` (cwd: `antigravity/desktop`) | Results screen shows the real Dev-1 data; no zod error | Error screen "The report couldn't be read" → open DevTools console, read the zod path, fix engine or schema |
| 3.3 | Schwan | `desktop/src/main/paths.ts` | Clear mock vars: `Remove-Item Env:AG_MOCK, Env:AG_MOCK_FIXTURE -ErrorAction SilentlyContinue` (cwd: `antigravity/desktop`). Add a temporary `console.log(paths.collectorScript(), paths.engine(), paths.baseline())` in `main/index.ts`, run `npm run dev` | Terminal shows three existing paths under the repo | Fix `repoRoot()` (§5.5) |
| 3.4 | Schwan | — | Remove the temporary log; commit | — | — |

### 6.5 Phase 4 — Wire UI → installer

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 4.1 | Tshedi | `engine/dist/engine/` | Build the engine exe: `.venv\Scripts\pyinstaller engine.spec --clean --noconfirm` (cwd: `antigravity/engine`) | `dist\engine\engine.exe --version` prints | §2.12; check `datas` in `engine.spec` |
| 4.2 | Schwan | — | Dev mode against the built exe: `$env:AG_ENGINE_EXE="1"; npm run dev` (cwd: `antigravity/desktop`); run one scan | Results appear; proves the exe works when spawned with the §4.7 arguments and cwd | Unset `AG_ENGINE_EXE` to go back to source mode; debug exe with §6.8 |
| 4.3 | Schwan | `desktop/src/main/resource-hashes.json` (§5.8, §7.8) | Generate the resource manifest: `node ..\installer\make-manifest.mjs` (cwd: `antigravity/desktop`) | JSON with SHA-256 for every file under `collector/` (shipped subset), `engine/dist/engine/`, `baseline/software-baseline.json` | Delete the file; the app logs "manifest missing" and refuses scans only when packaged |
| 4.4 | Schwan | `desktop/release/win-unpacked/` | Unpacked build: `npm run dist:dir` (cwd: `antigravity/desktop`) | `release\win-unpacked\resources\` contains `engine\engine.exe`, `collector\collector.ps1`, `baseline\software-baseline.json`; **no** `collector\tests` or `collector\mocks` | Check `extraResources` paths (§5.2); engine must be built first (4.1) |
| 4.5 | Schwan | — | Run `release\win-unpacked\Antigravity.exe` (cwd: `antigravity/desktop`); enter demo key; scan | Results in < 60 s | §6.8 rows 1–3 |

### 6.6 Phase 5 — First full end-to-end dev-mode run

Run as a team, on Dev-1, with the projector/screen everyone can see. Frank drives; Shakir, Tshedi and Schwan each watch their part.

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 5.1 | Frank | — | Turn Wi-Fi **off**. Start: `npm run dev` (cwd: `antigravity/desktop`), no mock variables set | Window opens | — |
| 5.2 | Shakir | `%APPDATA%\Antigravity\license.txt` | Delete any saved license (`Remove-Item $env:APPDATA\Antigravity\license.txt -ErrorAction SilentlyContinue`), restart the app | License screen shows | — |
| 5.3 | Shakir | — | Enter the expired token, then a tampered token, then demo key 0001 | Correct messages (§3.11 table), then accepted | Fix `verify.ts` |
| 5.4 | Frank | `%LOCALAPPDATA%\Antigravity\runs\<id>\scan.json` | Click "Start scan"; start a stopwatch | All phase messages appear in order (§4.8) | If progress stuck at 4%: phase markers missing (§6.8) |
| 5.5 | Tshedi | `…\runs\<id>\report.json/.html/.pdf` | Watch for the Results screen | Results in **< 60 s** non-elevated | Note timings per phase from the log; tune bands in `progress.ts` |
| 5.6 | Everyone | — | Check each of the 5 cards against Windows Security / Settings | Agreement | Log bugs with owner |
| 5.7 | Frank | — | Click "Open one-page action plan (PDF)", then "Open full report" | PDF opens, 1 page; HTML opens offline | §6.8 row 5 |
| 5.8 | Frank | — | Click "Scan again" | Second run completes; only one folder in `runs\` | Fix `runs.ts` |
| 5.9 | Schwan | — | Start a scan and click "Cancel" within 5 s; open Task Manager | Error screen "Scan cancelled"; no `powershell.exe` or `python.exe` from our run left | Fix kill-tree in `runProcess.ts` |
| 5.10 | Frank | — | Close the app; right-click terminal → Run as administrator; repeat 5.1, 5.4–5.5 | More rows rated; still < 60 s | — |
| 5.11 | Tshedi | — | `git tag v0.1-integrated; git push origin v0.1-integrated` (cwd: `antigravity`) | Tag on GitHub (target ~23:59 Day 1) | — |

### 6.7 Phase 6 — First installer

| # | Who | Files | Action (cwd) | Expected result | Rollback |
|---|---|---|---|---|---|
| 6.1 | Schwan | — | `git checkout v0.1-integrated` (cwd: `antigravity`) | Detached HEAD at the tag | — |
| 6.2 | Schwan | `desktop/release/*` | Full build: `powershell -NoProfile -ExecutionPolicy Bypass -File installer\build-all.ps1` (cwd: `antigravity`) | `CONTRACT OK` … `DONE -> desktop\release`; `Antigravity-Setup-0.1.0.exe` + `SHA256SUMS.txt` | Script stops at the failing step; fix on `fix/*`, re-tag `v0.1.1-integrated` |
| 6.3 | Schwan | — | Size check: `Get-Item desktop\release\Antigravity-Setup-*.exe \| Select Length` (cwd: `antigravity`) | ~100–150 MB | Engine folder missing → §6.8 row 3 |
| 6.4 | Schwan | VM | Clean-VM test §5.9, steps 1–14 minimum | All pass | Keep the dev-mode build as the demo fallback; log failures |
| 6.5 | Schwan | `docs/decisions.md` | Record: build version, time, VM result | One line added | — |
| 6.6 | Schwan | — | `git checkout main` (cwd: `antigravity`) | Back on `main` | — |

From now until 06:00, rebuild the installer after every merge to `main` that touches `collector/`, `engine/`, `baseline/` or `desktop/`; run §5.9 steps 1–14 on each.

### 6.8 Troubleshooting

| # | Symptom | Likely cause | Fix |
|---|---|---|---|
| 1 | **Packaged** app: "Scan failed" immediately; `last-error.txt` shows `ENOENT` or "cannot find path" | Path resolution: `paths.ts` using `__dirname`/`app.getAppPath()` (points inside `app.asar`) instead of `process.resourcesPath`; or `extraResources` `to:` names differ from what `paths.ts` expects | Compare `release\win-unpacked\resources\` with §5.4; always build packaged paths from `process.resourcesPath` (§5.5). Re-run `npm run dist:dir` and test before NSIS |
| 2 | Works in dev, fails packaged, error mentions `app.asar\…\collector.ps1` | Collector was bundled inside the asar via `files:` instead of `extraResources` | Scripts and exes must be in `extraResources` (§5.2); PowerShell can't read files inside an asar |
| 3 | **Python `engine.exe` not found** by the spawned process (`spawn … ENOENT`) | (a) `npm run dist` ran before `pyinstaller`, so `engine/dist/engine` didn't exist; (b) Defender quarantined `engine.exe`; (c) dev mode: `engine\.venv` not created on this machine | (a) Use `build-all.ps1` (it builds the engine first); (b) Windows Security → Protection history → restore; rebuild with `upx=False` (§2.12); (c) create the venv (§2.2) or set `AG_ENGINE_EXE=1` |
| 4 | `engine.exe` starts then exits 1: "Failed to load Python DLL" or templates not found | Spawned with the wrong `cwd`, or `_internal` folder not copied | `cwd` must be the engine folder (§4.7); check `resources\engine\_internal` exists; check `datas` in `engine.spec` |
| 5 | **PDF export fails in packaged mode** ("Open PDF" disabled, engine exit 3) | (a) ReportLab can't find data in the frozen build; (b) run folder not writable; (c) `report.html.j2` missing from bundle | (a) Run `resources\engine\engine.exe --in <scan> --out C:\temp\t` in a terminal to see the traceback; add `--collect-data reportlab` to the spec's `Analysis` (via `collect_data_files('reportlab')`) if needed; (b) check `%LOCALAPPDATA%\Antigravity\runs` ACL; (c) verify `datas` |
| 6 | "Open PDF" does nothing | `shell.openPath` returned an error (no PDF handler), or the previous run's PDF is still open and the folder couldn't be replaced | Show the returned error string; Edge is the default PDF viewer on Windows 10/11 — check Default apps. In `runs.ts`, ignore delete failures of old runs |
| 7 | **PowerShell blocked by execution policy**: stderr "running scripts is disabled on this system" | Machine policy set by Group Policy (`MachinePolicy`/`UserPolicy` scope), which overrides `-ExecutionPolicy Bypass` | Check `Get-ExecutionPolicy -List`. On dev machines: use a machine without the GPO. In product: UI shows "Your organisation's IT policy blocks scripts" (§3.12). Never call `Set-ExecutionPolicy` from the app |
| 8 | Collector exits with "Cannot be loaded because…" only for probe files | Files downloaded from GitHub zip carry Mark of the Web and policy is `RemoteSigned` | Use `-ExecutionPolicy Bypass` (the app always does); for manual runs: `Get-ChildItem collector -Recurse \| Unblock-File` (cwd: `antigravity`) |
| 9 | **Schema mismatch**: engine exit 2; UI shows all categories "Check failed" | Collector output and `scan.schema.json` disagree (renamed field, single-item array collapsed to object, date as `\/Date(…)\/`, BOM) | Run `engine\tools\validate.py scan <file>` (§6.3 step 2.3) to get the exact path. Common 5.1 causes and fixes in §3.8. If the schema itself must change: §0.10 |
| 10 | UI Error screen "The report couldn't be read" | `report.json` valid for the JSON schema but not for the renderer's zod schema (or vice versa) | DevTools console shows the zod path; align `reportSchema.ts` with `report.schema.json`; regenerate fixtures (§2.11 step 5) |
| 11 | Progress bar stuck at ~4% until results suddenly appear | No `AG-PHASE:` lines arriving: collector run with `-DryRun`, markers not merged (§3.2), or main not wiring `onLine` | Run the collector manually with `-OutputPath` and watch stdout; check `runCollector` passes `onLine` |
| 12 | Scan times out at 45 s | Slow probe (big uninstall list, `Get-WinEvent` on a huge log, `reagentc` hanging) | Run `-Only <Probe>` per probe and read `duration_ms` (§3.9); use `-MaxEvents 1` everywhere; skip `reagentc` when not admin |
| 13 | Nested values in `scan.json` show as `"System.Collections.Hashtable"` | `ConvertTo-Json` depth default (2) | `-Depth 8` (§3.8) |
| 14 | `npm ci` hangs/fails at the venue on `electron` postinstall: "getaddrinfo ENOTFOUND github.com" | **Electron binary download** — cache empty on this machine | §1.6: restore `%LOCALAPPDATA%\electron\Cache` from Schwan's USB, then `npm ci --prefer-offline`. Last resort: `ELECTRON_SKIP_BINARY_DOWNLOAD=1` + manual unzip (§1.6 step 5) |
| 15 | `npm run dist` fails downloading `nsis` or `winCodeSign` | electron-builder cache empty | Restore `%LOCALAPPDATA%\electron-builder\Cache` from USB (§1.6 step 4) |
| 16 | `pip install` fails offline | Wheel missing from `.offline\wheelhouse` (e.g. built on a different Python minor version) | Everyone uses Python 3.12 (§1.1). Copy Schwan's wheelhouse from USB; `pip install --no-index --find-links` (§1.8) |
| 17 | Packaged app opens to a white window | Renderer path wrong in production (`loadURL` used instead of `loadFile` in packaged mode) | In `main/index.ts`: dev → `loadURL(process.env['ELECTRON_RENDERER_URL'])`; packaged → `loadFile(join(__dirname, '../renderer/index.html'))` (electron-vite convention) |
| 18 | `Get-MpComputerStatus` fails on Dev-2 with a COM error | Defender service stopped or third-party AV primary | Expected; handled per §3.6 (finding, not failure). If it becomes `failed`, check the `WinDefend` service fallback is merged |
| 19 | Merge conflicts in `package-lock.json` | Two people added dependencies | Take `main`'s lockfile, then the PR owner re-runs `npm install <their dep>@<pin>` and commits the new lockfile |
| 20 | Landing build fails on Vercel | Node version mismatch or Root Directory not `landing` | §4.13 steps 3–5; previous deployment stays live meanwhile |

---

## §7 Cybersecurity test plan

This plan tests the **finished** product (installer built from `v1.0.0-demo`, or the latest integrated build) on Schwan's clean VM (§5.9) unless a test says otherwise. It proves the claims we make to judges: the agent is read-only, keeps data local, verifies licences offline, runs with least privilege, and tells the truth in its report.

### 7.1 How to run this plan

1. Run on the **clean VM**, reverted to `clean-baseline` before each block (RO, PRV, INS especially).
2. Install the build under test as the **standard user** (§5.9 steps 1–6).
3. Fill the **Pass/Fail** column with ✅ / ❌ and initials. Paste evidence (screenshots, command output) into `docs/security-evidence/<test-id>.*` (git-ignored if it contains machine details; commit a summary in `docs/security-results.md`).
4. Priority: every **[MVP]** test must be ✅ before 06:00 Day 2. **[STRETCH]** tests run only if time allows.
5. Owner of the plan: **Shakir** (security lead for the pitch). Execution split shown in each section.
6. Timing (§8.4, §8.6): **first pass Day 1 00:00–02:00** (RO-01..03, LIC-01..07, PRV-01..02, RPT-01..08); **final pass Day 2 08:00–09:00 on RC1** (RO-01..03, LIC-08, PRV-01, PRV-04, LP-02..05, TMP-01..04, INS-03..06).

### 7.2 Test tooling (prepare at home)

All tools are free, Microsoft-provided or built in, and must be downloaded **before travel** into `antigravity/.offline/tools/` (§1.5).

| Tool | Version | Use | Source |
|---|---|---|---|
| Process Monitor (Procmon) | latest Sysinternals | File/registry/network activity per process (RO, PRV) | Microsoft Sysinternals |
| Strings | latest Sysinternals | Look for secrets in binaries (LIC) | Microsoft Sysinternals |
| Sigcheck | latest Sysinternals | Check manifest `requestedExecutionLevel`, signatures (LP, INS) | Microsoft Sysinternals |
| `reg`, `auditpol`, `icacls`, `pktmon` | built in | Snapshots, auditing, ACLs, packet capture | Windows |
| 7-Zip | baseline version | List installer contents (INS) | 7-zip.org |
| `@electron/asar` CLI | comes with electron-builder (`desktop\node_modules\.bin\asar`) | Extract `app.asar` (LIC) | npm cache |

New helper scripts, stored in `tools/security/`:

| File | Purpose |
|---|---|
| `Snapshot-State.ps1` | Capture system state to a folder (§7.3) |
| `Compare-State.ps1` | Diff two snapshots and print changes per area |
| `Analyze-Procmon.ps1` | Filter a Procmon CSV for write/network operations by our processes |
| `ag-procmon.pmc` | Saved Procmon filter (Process Name is `Antigravity.exe`, `powershell.exe`, `engine.exe`, `reagentc.exe`, `taskkill.exe`) |

`tools/security/Snapshot-State.ps1` (runs **elevated on the VM only** — it is a test tool, not part of the product):

```powershell
# tools/security/Snapshot-State.ps1   usage: -Out C:\sec\before
param([Parameter(Mandatory)][string]$Out)
New-Item -ItemType Directory -Force $Out | Out-Null
reg export HKLM\SOFTWARE                               "$Out\hklm-software.reg" /y | Out-Null
reg export HKLM\SYSTEM\CurrentControlSet\Services      "$Out\hklm-services.reg" /y | Out-Null
reg export HKCU\Software                               "$Out\hkcu-software.reg" /y | Out-Null
Get-Service | Sort-Object Name | Select-Object Name, Status, StartType | Export-Csv "$Out\services.csv" -NoTypeInformation
Get-ScheduledTask | Sort-Object TaskPath, TaskName | Select-Object TaskPath, TaskName, State | Export-Csv "$Out\tasks.csv" -NoTypeInformation
Get-MpPreference | Select-Object DisableRealtimeMonitoring, EnableControlledFolderAccess,
    AttackSurfaceReductionRules_Ids, AttackSurfaceReductionRules_Actions, ExclusionPath, ExclusionProcess |
    ConvertTo-Json -Depth 4 | Set-Content "$Out\defender-prefs.json"
Get-BitLockerVolume -ErrorAction SilentlyContinue | Select-Object MountPoint, ProtectionStatus, VolumeStatus |
    ConvertTo-Json | Set-Content "$Out\bitlocker.json"
@{ restorePoints = @(Get-ComputerRestorePoint -ErrorAction SilentlyContinue).Count
   shadowCopies  = @(Get-CimInstance Win32_ShadowCopy).Count } | ConvertTo-Json | Set-Content "$Out\recovery.json"
Get-ExecutionPolicy -List | Out-String | Set-Content "$Out\execpolicy.txt"
Get-NetFirewallRule | Sort-Object Name | Select-Object Name, Enabled, Direction, Action | Export-Csv "$Out\firewall.csv" -NoTypeInformation
Get-ChildItem "$env:USERPROFILE\Documents","$env:USERPROFILE\Desktop" -Recurse -File -ErrorAction SilentlyContinue |
    Select-Object FullName, Length, LastWriteTimeUtc | Export-Csv "$Out\userfiles.csv" -NoTypeInformation
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue |
    Out-String | Set-Content "$Out\run-keys.txt"
Write-Host "Snapshot written to $Out"
```

`tools/security/Compare-State.ps1`:

```powershell
# tools/security/Compare-State.ps1   usage: -Before C:\sec\before -After C:\sec\after
param([string]$Before, [string]$After)
Get-ChildItem $Before -File | ForEach-Object {
  $b = Get-Content $_.FullName; $a = Get-Content (Join-Path $After $_.Name)
  $d = Compare-Object $b $a
  if ($d) { Write-Host "== $($_.Name): $($d.Count) changed lines" -ForegroundColor Yellow; $d | Select-Object -First 40 | Format-Table -AutoSize }
  else    { Write-Host "== $($_.Name): no change" -ForegroundColor Green }
}
```

### 7.3 Read-only verification (RO)

**Method.** Windows changes its own registry constantly, so a raw diff is never empty. We use a **control pair**: two snapshots with *no* scan in between, taken the same time apart as the real test. The scan pair must show **no changes beyond the control pair's noise**, and Procmon must show **zero write operations by the collector** outside its own output file.

Executed by **Shakir** (with Schwan's VM). All RO tests run twice: as standard user and elevated (`Run as administrator`).

**Commands used by the RO tests** (cwd: `C:\sec` on the VM, elevated PowerShell for snapshots and auditing):

```powershell
# RO-SETUP — once per VM revert, after installing Antigravity and launching it once
auditpol /set /subcategory:"Process Creation" /success:enable
reg add HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System\Audit /v ProcessCreationIncludeCmdLine_Enabled /t REG_DWORD /d 1 /f
reg add HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging /v EnableScriptBlockLogging /t REG_DWORD /d 1 /f

# CONTROL PAIR (no scan)
.\Snapshot-State.ps1 -Out C:\sec\ctl-before
Start-Sleep -Seconds 60            # roughly one scan's duration
.\Snapshot-State.ps1 -Out C:\sec\ctl-after
.\Compare-State.ps1 -Before C:\sec\ctl-before -After C:\sec\ctl-after > C:\sec\ctl-diff.txt

# SCAN PAIR
.\Snapshot-State.ps1 -Out C:\sec\scan-before
$t0 = Get-Date
.\Procmon64.exe /AcceptEula /Quiet /Minimized /BackingFile C:\sec\scan.pml /LoadConfig C:\sec\ag-procmon.pmc
#   >>> now run one full scan in the Antigravity app and wait for Results <<<
.\Procmon64.exe /Terminate
.\Snapshot-State.ps1 -Out C:\sec\scan-after
.\Compare-State.ps1 -Before C:\sec\scan-before -After C:\sec\scan-after > C:\sec\scan-diff.txt
.\Procmon64.exe /OpenLog C:\sec\scan.pml /SaveAs C:\sec\scan.csv
.\Analyze-Procmon.ps1 -Csv C:\sec\scan.csv
```

`tools/security/Analyze-Procmon.ps1`:

```powershell
# tools/security/Analyze-Procmon.ps1
param([string]$Csv)
$write = 'WriteFile','SetDispositionInformationFile','SetRenameInformationFile','SetBasicInformationFile',
         'RegSetValue','RegCreateKey','RegDeleteKey','RegDeleteValue','RegSetInfoKey'
$allowed = @(                                             # expected, documented writes
  [regex]::Escape("$env:LOCALAPPDATA\Antigravity\"),       # run folder, logs
  [regex]::Escape("$env:APPDATA\Antigravity\"),            # Electron userData, license.txt
  [regex]::Escape("$env:LOCALAPPDATA\Microsoft\Windows\PowerShell\")   # PowerShell runtime caches (not our script)
)
$rows = Import-Csv $Csv
$w = $rows | Where-Object { $_.Operation -in $write -and $_.Result -eq 'SUCCESS' }
$unexpected = $w | Where-Object { $p = $_.Path; -not ($allowed | Where-Object { $p -match "^$_" }) }
"Write ops total: $($w.Count); unexpected: $(@($unexpected).Count)"
$unexpected | Group-Object 'Process Name', Operation, Path | Sort-Object Count -Descending |
  Select-Object Count, Name -First 50 | Format-Table -AutoSize
$net = $rows | Where-Object { $_.Operation -match '^(TCP|UDP) ' }
"Network ops by our processes: $(@($net).Count)"
$net | Select-Object 'Process Name', Operation, Path -First 20 | Format-Table -AutoSize
```

```powershell
# AUDIT-LOG REVIEW (after the scan)
Get-WinEvent -FilterHashtable @{ LogName='Security'; Id=4688; StartTime=$t0 } |
  Where-Object { $_.Message -match 'Antigravity|powershell|engine\.exe|reagentc|taskkill' } |
  ForEach-Object { ($_.Message -split "`n" | Select-String 'New Process Name|Process Command Line|Creator Process Name|Token Elevation Type') -join ' | ' }

Get-WinEvent -FilterHashtable @{ LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104; StartTime=$t0 } |
  ForEach-Object { $_.Message } |
  Select-String -Pattern '\b(Set|New|Remove|Add|Clear|Enable|Disable|Start|Stop|Restart|Install|Uninstall|Register)-\w+' -AllMatches |
  ForEach-Object { $_.Matches.Value } | Sort-Object -Unique
```

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| RO-01 | [MVP] | System state is unchanged by a scan | VM reverted; app installed and licensed; RO-SETUP done | Run CONTROL PAIR, then SCAN PAIR (above). Compare `scan-diff.txt` with `ctl-diff.txt` | `services.csv`, `tasks.csv`, `defender-prefs.json`, `bitlocker.json`, `recovery.json`, `execpolicy.txt`, `firewall.csv`, `run-keys.txt`, `userfiles.csv`: **no change**. Registry `.reg` diffs contain only keys that also change in the control pair, plus (if first run) Electron's own entries under `HKCU\Software\…\Antigravity` | ☐ |
| RO-02 | [MVP] | Collector and engine perform no writes outside their output | As RO-01 | Run `Analyze-Procmon.ps1` on the scan capture | **Unexpected writes: 0.** `powershell.exe` writes only `…\runs\<id>\scan.json`; `engine.exe` writes only `report.json/.html/.pdf` in the same folder. No `Reg*` write operations by `powershell.exe`, `engine.exe` or `reagentc.exe` | ☐ |
| RO-03 | [MVP] | No state-changing commands executed | As RO-01 | Run AUDIT-LOG REVIEW | Process tree only: `Antigravity.exe → powershell.exe (-File …collector.ps1 -OutputPath … -RunId …)`, `powershell.exe → reagentc.exe /info` (elevated only), `Antigravity.exe → engine.exe --in … --out … --baseline …`. Script block verbs found: **none** except `New-Object` (allow-listed COM read, §3.7) | ☐ |
| RO-04 | [MVP] | Static read-only guarantee holds on the shipped files | Final build unpacked | `powershell -NoProfile -ExecutionPolicy Bypass -File collector\tests\Test-ReadOnly.ps1` (cwd: `antigravity`) **and** compare `release\win-unpacked\resources\collector\` file hashes with the repo copies | `READ-ONLY OK`; shipped scripts identical to tested scripts | ☐ |
| RO-05 | [MVP] | Repeat RO-01..03 elevated | VM reverted; app started via Run as administrator | Repeat RO-01..03 | Same results; elevated rights do not cause any write | ☐ |
| RO-06 | [MVP] | `Win32_Product` never queried (it triggers MSI repairs) | RO-SETUP done | After a scan: `Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MsiInstaller'; StartTime=$t0}` | **No** MsiInstaller events (event 1035 would indicate reconfiguration) | ☐ |
| RO-07 | [STRETCH] | No Volume Shadow Copy or backup jobs triggered | As RO-01 | `Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='VSS'; StartTime=$t0}`; check `recovery.json` diff | No VSS create events; shadow copy count unchanged | ☐ |

### 7.4 License security (LIC)

Executed by **Shakir**. Tokens used: demo `AG-DEMO-0001`, the expired token (§3.11 step 5), and hand-modified variants.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| LIC-01 | [MVP] | Malformed input rejected | Fresh install | Enter `hello`, empty string, `AG1.`, a 5 000-character string | "That doesn't look like an Antigravity key…"; app stays responsive | ☐ |
| LIC-02 | [MVP] | Tampered payload rejected | Valid demo token copied to Notepad | Decode the middle segment (base64url), change `exp` to a later date, re-encode, paste back, enter | "This key isn't valid." (`bad_signature` in log) | ☐ |
| LIC-03 | [MVP] | Signature swap rejected | Two valid tokens | Combine payload of token 1 with signature of token 2 | "This key isn't valid." | ☐ |
| LIC-04 | [MVP] | Expired token rejected | Expired test token | Enter it | "This key expired on {date}…" | ☐ |
| LIC-05 | [MVP] | Unknown key id rejected | Valid token | Change `kid` in payload (re-encode), enter | "This key isn't valid." | ☐ |
| LIC-06 | [MVP] | Stored licence re-verified on every launch | Licensed app | Close app; edit `%APPDATA%\Antigravity\license.txt` (change one character); relaunch | License screen shown, not Results | ☐ |
| LIC-07 | [MVP] | Scan is gated in the main process, not only the UI | **Dev build** (`npm run dev`) with no licence | Open DevTools (Ctrl+Shift+I) → Console → `await window.antigravity.runScan()` | Returns `{ ok: false, stage: "license" }`; no `powershell.exe` spawned (Task Manager) | ☐ |
| LIC-08 | [MVP] | No private key or secrets in the shipped app | Final build | Extract and search (commands below) | Zero hits for `PRIVATE KEY`, `.antigravity-private`, `BEGIN EC`, `sk_`, `api_key`, `password`. Only `BEGIN PUBLIC KEY` found | ☐ |
| LIC-09 | [MVP] | No private key in Git history | Repo clone | `git log --all -p -S "PRIVATE KEY"` (cwd: `antigravity`) | No output | ☐ |
| LIC-10 | [MVP] | Licence check works offline | VM network disconnected | Fresh install, enter demo key | Accepted with no network | ☐ |
| LIC-11 | [STRETCH] | Clock rollback (known limitation) | Expired token | Set VM clock back before `exp`; enter token | **Accepted** — documented limitation of offline checks (§7.10, row "Licence bypass"). Record, don't fix | ☐ |

LIC-08 commands:

```powershell
# cwd: antigravity/desktop
.\node_modules\.bin\asar extract release\win-unpacked\resources\app.asar ..\out\asar-x
Get-ChildItem ..\out\asar-x, release\win-unpacked\resources -Recurse -File |
  Select-String -Pattern 'PRIVATE KEY','antigravity-private','BEGIN EC','api_key','password','sk_' -SimpleMatch |
  Select-Object Path, LineNumber, Line -First 20
..\.offline\tools\strings64.exe -accepteula -n 8 release\win-unpacked\Antigravity.exe | Select-String 'PRIVATE KEY'
..\.offline\tools\strings64.exe -accepteula -n 8 -s release\win-unpacked\resources\engine | Select-String 'PRIVATE KEY'
```

(Demo tokens appearing in `docs/` are fine — they are public by design and only unlock a free, local tool.)

### 7.5 Data privacy / POPIA (PRV)

Executed by **Schwan** (VM) and **Shakir**. Our POPIA position: we collect the minimum system facts needed for five checks, nothing identifies a person, and nothing leaves the PC.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| PRV-01 | [MVP] | No network activity during the whole user journey | VM **with network connected**; Procmon running with `ag-procmon.pmc` | Launch app → enter licence → scan → open PDF and HTML → close. Run `Analyze-Procmon.ps1` | "Network ops by our processes: **0**" for `Antigravity.exe`, `powershell.exe`, `engine.exe` | ☐ |
| PRV-02 | [MVP] | App works identically with all outbound traffic blocked | VM, network connected | Elevated: `New-NetFirewallRule -DisplayName "AG-block" -Direction Outbound -Action Block -Program "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe"`; same for `…\resources\engine\engine.exe` and `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`. Run full journey. Remove rules after: `Remove-NetFirewallRule -DisplayName "AG-block"` | Same results, same timings, no errors | ☐ |
| PRV-03 | [STRETCH] | Host-level capture confirms PRV-01 | VM, network connected, no other apps open | Elevated: `pktmon start --capture --pkt-size 0 --file-name C:\sec\net.etl`; run journey; `pktmon stop`; `pktmon etl2txt C:\sec\net.etl --out C:\sec\net.txt`. Compare against a 60-s idle capture | No traffic beyond the idle baseline (Windows Update, Defender cloud, etc. appear in both) | ☐ |
| PRV-04 | [MVP] | No personal data in collected or reported data | Completed scan | `$f = Get-ChildItem "$env:LOCALAPPDATA\Antigravity\runs\*\*" -Include *.json,*.html; Select-String -Path $f -Pattern $env:USERNAME, $env:COMPUTERNAME, 'C:\\Users', '@', '\b\d{1,3}(\.\d{1,3}){3}\b', '([0-9A-F]{2}[:-]){5}[0-9A-F]{2}' ` (cwd: any) | No matches (software publisher names containing "@" are the only acceptable exception — inspect each hit) | ☐ |
| PRV-05 | [MVP] | Only contract fields are collected | Completed scan | Validate `scan.json` against the schema with `additionalProperties: false` checked manually: list top-level and section keys and compare with §0.6 | Keys match §0.6 exactly; no file names, user names, email, browser or document data | ☐ |
| PRV-06 | [MVP] | Data stays private to the user | Completed scan | `icacls "$env:LOCALAPPDATA\Antigravity\runs"` and `icacls "$env:APPDATA\Antigravity"` | Access only for the current user, `SYSTEM`, `Administrators` (inherited from the profile); no `Everyone`/`Users` | ☐ |
| PRV-07 | [MVP] | Report shared only by explicit user action | App open on Results | Inspect UI and code: no email, upload, "share" or auto-open-in-browser-on-scan behaviour; PDF/HTML open only on button click | Confirmed. The only way data leaves is the user copying a file themselves | ☐ |
| PRV-08 | [MVP] | Minimal retention | Two scans done | Count folders in `runs\` | Exactly one (latest only, §5.6 step 8) | ☐ |
| PRV-09 | [MVP] | Data removed on uninstall | After uninstall | Check `%APPDATA%\Antigravity`, `%LOCALAPPDATA%\Antigravity` | Both gone (§5.3) | ☐ |
| PRV-10 | [MVP] | Renderer cannot reach the network | Dev build, DevTools open | Console: `fetch('https://example.com')` | Blocked by CSP `connect-src 'none'` (§4.4) | ☐ |
| PRV-11 | [MVP] | Spellchecker doesn't fetch dictionaries | Code review | Confirm `webPreferences.spellcheck: false` in `main/index.ts` (§4.4) | Present | ☐ |

**Honest note for the pitch:** `host.hostname_hash` is a salted hash with a fixed salt — **pseudonymous, not anonymous**; someone with the hash and a list of candidate names could match it. It never leaves the PC and isn't used for any scoring. **Default:** keep for MVP (display only); **[STRETCH]** drop the field in contract 1.1 via §0.10.

### 7.6 Report integrity (RPT)

Executed by **Tshedi** (engine tests) and **Frank** (rendering). Most are automated in `engine/tests/test_integrity.py` (§2.10) and `desktop` vitest.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| RPT-01 | [MVP] | "unavailable" is never rendered as "failed" (and vice versa) | Fixtures incl. non-admin and Home edition | `pytest -q tests/test_integrity.py -k status_mapping` (cwd: `antigravity/engine`); in desktop `npm run test` | For every collector section with `status: unavailable`, report shows `unavailable` (or rated amber for Home BitLocker, §2.5.4) — **never** `failed`. HTML contains "Not checked" not "Check failed" for those. UI badge text matches (§4.9.3) | ☐ |
| RPT-02 | [MVP] | Every finding cites evidence | All fixtures + a real VM scan | Test: for each category with status red/amber, `len(evidence) ≥ 1` **and** at least one evidence row has the same status as the category | Holds for all fixtures and real scans | ☐ |
| RPT-03 | [MVP] | Every red/amber finding has a fix | As RPT-02 | Test: red/amber ⇒ `fix_ids` non-empty, every id exists in `fixes[]` | Holds | ☐ |
| RPT-04 | [MVP] | RAG matches the scoring rules | §2.10 suite | `pytest -q` (cwd: `antigravity/engine`) — every rule in §2.5 has a test | All green; boundaries (30/31, 60/61 days) correct | ☐ |
| RPT-05 | [MVP] | RAG matches reality on a live machine | VM elevated, Tamper Protection off | Turn Defender real-time protection off in Windows Security; scan; turn back on; scan | First scan: protection **red**, `enable-defender` in top fixes; second: protection green/amber | ☐ |
| RPT-06 | [MVP] | Report invariants | All fixtures | Test: exactly 5 categories in fixed order; `overall` = worst rated; `top_fixes` ≤ 3, ⊆ `fixes[].id`, ranked per §0.8 | Holds | ☐ |
| RPT-07 | [MVP] | Injected text from the PC is never executed | Fixture with software name `<script>alert(1)</script><img src=x onerror=alert(2)>` | Run engine → open HTML in Edge; load fixture in app (mock mode) | Text shown literally; no dialog; HTML source shows escaped `&lt;script&gt;` | ☐ |
| RPT-08 | [MVP] | PDF agrees with app and HTML | One real scan | Compare overall status, 5 category statuses and top-3 titles across UI, HTML and PDF | Identical | ☐ |
| RPT-09 | [MVP] | Partial failures are disclosed | Mock `probe-throws` (§3.10) → engine → app | Run | Software card "Check failed"; summary ends "Some checks couldn't run."; other categories rated normally | ☐ |
| RPT-10 | [MVP] | Report doesn't overclaim | Review | Footer says "Guidance only, not a full audit" in HTML and PDF (§4.10–4.11) | Present | ☐ |

### 7.7 Least privilege (LP)

What needs elevation (from §3.5):

| Data point | Needs admin | Non-admin behaviour |
|---|---|---|
| `backup.windows_backup_last_success` | Yes | `null` → grey row |
| `backup.shadow_copy_count` | Yes | `null` → grey row |
| `protection.bitlocker` (full detail) | Yes | COM fallback gives on/off only; if that fails → `unavailable` |
| `recovery.winre_enabled` | Yes | `null` → grey row |
| `recovery.restore_point_count`, `latest_restore_point` | Yes | `null` → grey rows |
| Everything else | No | Full data |

Executed by **Schwan**.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| LP-01 | [MVP] | Install needs no admin | VM, standard user | Run installer | No UAC prompt; installs to `%LOCALAPPDATA%\Programs\Antigravity` | ☐ |
| LP-02 | [MVP] | App runs non-elevated by default | Installed | Launch from Start menu; Task Manager → Details → add column **Elevated** | `Antigravity.exe`, `powershell.exe`, `engine.exe` all **No** | ☐ |
| LP-03 | [MVP] | Manifest requests no elevation | Final build | `.offline\tools\sigcheck64.exe -accepteula -m desktop\release\win-unpacked\Antigravity.exe` (cwd: `antigravity`) and same for `resources\engine\engine.exe` | `requestedExecutionLevel level="asInvoker"` for both | ☐ |
| LP-04 | [MVP] | Non-elevated scan degrades gracefully | Standard user | Scan | Completes < 60 s; admin hint shown; grey rows exactly for the admin-only data points above; no `failed` caused by missing rights | ☐ |
| LP-05 | [MVP] | App never self-elevates | RO-SETUP auditing on | After LP-04, run the 4688 query (§7.3) and read **Token Elevation Type** | `%%1938` (limited) for all our processes; no UAC prompt seen at any time | ☐ |
| LP-06 | [MVP] | Elevated run is still read-only | — | Covered by RO-05 | — | ☐ |
| LP-07 | [MVP] | Collector launched with minimal flags | Procmon or 4688 log | Inspect command line | `-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File …` — no `-EncodedCommand`, no `-WindowStyle Hidden` (§3.12) | ☐ |

### 7.8 Tamper resistance (TMP)

**Threat model in one paragraph.** Antigravity installs per-user into `%LOCALAPPDATA%\Programs\Antigravity`, which the logged-in user — and any malware running as that user — can modify. An attacker who can already run code as the user gains nothing by tampering with us *while we run non-elevated*. The real risks are: (1) **integrity** — a modified baseline, engine or collector makes an unsafe PC look green and gives false reassurance; (2) **elevation** — if the owner later chooses *Run as administrator*, a replaced `collector.ps1` or `engine.exe` would run with admin rights.

**MVP mitigation — resource hash manifest (§5.8).** At build time `installer/make-manifest.mjs` writes SHA-256 hashes of every shipped file under `resources\collector`, `resources\engine` and `resources\baseline` into `resource-hashes.json`, which is compiled into `app.asar`. Before every scan, main re-hashes those files; any mismatch, missing or extra executable file → scan refused with "Some app files have been changed. Please reinstall Antigravity." Cost: ~40 lines, < 1 s per scan.

**Out of scope for the hackathon (say so honestly):** the manifest lives in `app.asar`, which is also user-writable, so a determined attacker can patch both. Real fixes are: per-machine install in `Program Files` (admin-only writable), Authenticode-signed binaries, Electron's asar-integrity and other fuses, and a signed baseline. These are post-hackathon work.

Executed by **Schwan** and **Shakir**.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| TMP-01 | [MVP] | Modified baseline detected | Installed, licensed | Edit `resources\baseline\software-baseline.json` (lower Chrome's `min_safe_version`); scan | Scan refused with the reinstall message; nothing spawned | ☐ |
| TMP-02 | [MVP] | Modified collector detected | As TMP-01 (reinstall first) | Append a comment line to `resources\collector\probes\Patch.ps1`; scan | Refused | ☐ |
| TMP-03 | [MVP] | Replaced engine detected | Reinstall | Replace `resources\engine\engine.exe` with a copy of `notepad.exe` renamed; scan | Refused; Notepad never starts | ☐ |
| TMP-04 | [MVP] | Extra script dropped in detected | Reinstall | Create `resources\collector\probes\Evil.ps1` (empty); scan | Refused (the collector dot-sources every `probes\*.ps1`, so an extra file matters) | ☐ |
| TMP-05 | [MVP] | Documented gap: `app.asar` modification | Reinstall | Modify `app.asar` (e.g. extract, change a UI string, repack) | **Not detected** — expected for MVP. Record as known gap; mitigation listed in §7.10 | ☐ |
| TMP-06 | [STRETCH] | Electron run-as-node abuse | Installed | `$env:ELECTRON_RUN_AS_NODE=1; & "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe" -e "console.log(1)"` | MVP: prints `1` (documented gap). With fuses disabled via `@electron/fuses` (STRETCH): ignored | ☐ |
| TMP-07 | [MVP] | `report.json` can't be swapped mid-scan to mislead | Code review | Confirm main reads `report.json` immediately after engine exit and the UI uses that in-memory copy; re-opening history is not offered | Confirmed (scan history is cut, §0 MVP) | ☐ |
| TMP-08 | [STRETCH] | Mock hooks not reachable in product | Installed | Confirm `collector\mocks\` absent; consider making `-MockFile` ignored unless `AG_DEV=1` | Mocks absent (§5.2); `-MockFile` guard if time | ☐ |

### 7.9 Installer security (INS)

Executed by **Schwan**.

| ID | Tag | Objective | Preconditions | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|---|---|
| INS-01 | [MVP] | Unsigned-installer warning is handled calmly in the demo | Installer downloaded through Edge on the VM (to get Mark of the Web) | Run it; follow §5.7 (More info → Run anyway). Time it | Rehearsed; < 10 s; narrated line ready: "Unsigned for the hackathon — signing is the first post-event step" | ☐ |
| INS-02 | [MVP] | Installer integrity can be checked | Published `SHA256SUMS.txt` | `Get-FileHash .\Antigravity-Setup-*.exe -Algorithm SHA256` (cwd: download folder) | Matches the published hash | ☐ |
| INS-03 | [MVP] | No bundled unwanted software | Final build | `7z l desktop\release\Antigravity-Setup-*.exe` (cwd: `antigravity`) and `Get-ChildItem desktop\release\win-unpacked -Recurse -Include *.exe,*.dll,*.ps1,*.bat,*.cmd,*.vbs,*.js -File \| Select-Object -Expand FullName` compared with `installer/expected-files.txt` (Appendix C) | Only expected files: Electron runtime, `Antigravity.exe`, `engine.exe` + `_internal`, our `.ps1` files, uninstaller. No toolbars, updaters, drivers, services, extra installers | ☐ |
| INS-04 | [MVP] | Install leaves no persistence | Snapshot before install (§7.2) | Install, launch, close; snapshot; compare | New: install folder, Start menu/desktop shortcuts, HKCU uninstall key, `%APPDATA%\Antigravity`. **None of:** services, scheduled tasks, Run keys, startup folder entries, firewall rules, file associations | ☐ |
| INS-05 | [MVP] | Clean uninstall | After INS-04 | Uninstall via Settings → Apps; snapshot; compare with pre-install snapshot | All of INS-04's "New" items gone, including `Get-ChildItem HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall \| Where-Object { (Get-ItemProperty $_.PSPath).DisplayName -like 'Antigravity*' }` returning nothing; `%LOCALAPPDATA%\Antigravity` removed (§5.3) | ☐ |
| INS-06 | [MVP] | Defender doesn't flag the build | VM with Defender real-time on | Install + scan; check Protection history; also `Start-MpScan -ScanType CustomScan -ScanPath "$env:LOCALAPPDATA\Programs\Antigravity"` (VM only — tester action, not product) | No detections | ☐ |
| INS-07 | [MVP] | Installer doesn't need or request network | VM network disconnected | Install | Completes; no download step | ☐ |
| INS-08 | [STRETCH] | Second-opinion malware scan | Network available | Upload the installer to a multi-engine scanner (it's our own public binary) | No or only generic "unsigned/uncommon" heuristics; record result for Q&A | ☐ |

### 7.10 Threat model

> **Source note:** the Idea Canvas was not available when this section was written. The "Why it's secure" column uses five claims **inferred from the project brief** (S1–S5 below). Before the pitch, replace each S-label with the exact canvas wording and adjust any row that no longer matches.

| Ref | "Why it's secure" claim (inferred — replace with canvas wording) |
|---|---|
| S1 | Strictly read-only: it never changes a setting on your PC |
| S2 | Local-only and POPIA-minimal: nothing leaves the machine; no personal data collected |
| S3 | Licences are signed tokens verified offline |
| S4 | No auto-remediation: the owner stays in control of every fix |
| S5 | Least privilege: runs as a normal user; admin is optional |

| # | Asset | Threat | Mitigation | Tests | MVP status | Claim |
|---|---|---|---|---|---|---|
| 1 | The owner's PC configuration | Our agent changes settings (bug or malicious build) | PowerShell allow-list + AST static check; no write cmdlets; no `Win32_Product`; no remediation code exists at all | RO-01..07 | ✅ Mitigated | S1, S4 |
| 2 | The owner's PC configuration | Elevated run amplifies any bug | Same read-only code path elevated or not; elevated run tested | RO-05, LP-06 | ✅ Mitigated | S1, S5 |
| 3 | Scan data (`scan.json`, reports) | Exfiltration over the network | No network code in collector/engine; CSP `connect-src 'none'`; no updater, telemetry or crash reporter; spellcheck off | PRV-01..03, PRV-10, PRV-11 | ✅ Mitigated | S2 |
| 4 | Scan data | Collection of personal data | Contract limited to system facts (§0.6); hashed hostname; no user/file/IP data; automated grep | PRV-04, PRV-05 | ✅ Mitigated (hostname hash is pseudonymous — see §7.5 note) | S2 |
| 5 | Scan data at rest | Other local users read it | Stored in the user's own profile with default user-only ACLs; latest run only; removed on uninstall | PRV-06, PRV-08, PRV-09 | ✅ Mitigated | S2 |
| 6 | Report sharing | Report sent somewhere without consent | No share/email/upload features; files open only on click | PRV-07 | ✅ Mitigated | S2, S4 |
| 7 | Licence system | Forged or edited tokens | Ed25519 signature over prefix + payload; strict parsing; verified in main on launch and before every scan | LIC-01..07, LIC-10 | ✅ Mitigated | S3 |
| 8 | Licence system | Private signing key leaked | Key generated and kept off-repo on Shakir's machine, backed up in a password manager; repo and binary scanned | LIC-08, LIC-09 | ✅ Mitigated | S3 |
| 9 | Licence system | Bypass by clock rollback or patching the app | None in MVP (offline checks can't prevent this) | LIC-11, TMP-05 | ⚠️ Accepted risk — low value target (free local tool); online activation out of scope | S3 |
| 10 | Report trustworthiness | Wrong status (false green) from rule bugs | Rule-per-test suite, boundary tests, live toggle test, invariants | RPT-02..06, RPT-08 | ✅ Mitigated | — (supports S4: owner acts on accurate advice) |
| 11 | Report trustworthiness | Missing data shown as failure, or hidden | Separate `unavailable`/`failed` paths in collector and engine; summary discloses failures | RPT-01, RPT-09 | ✅ Mitigated | S5 (non-admin runs are honest about gaps) |
| 12 | Report trustworthiness | Malicious registry text (app names) executes in report | Jinja autoescape; React escaping; no `dangerouslySetInnerHTML`; no scripts in HTML report | RPT-07 | ✅ Mitigated | S1 |
| 13 | Shipped resources (baseline, collector, engine) | Local malware edits them → false green, or code runs elevated later | SHA-256 resource manifest checked before every scan | TMP-01..04 | ✅ Mitigated for these files | S1, S5 |
| 14 | `app.asar` and manifest | Patched together by a determined local attacker | None in MVP | TMP-05 | ⚠️ Out of scope — next: per-machine install in Program Files, code signing, Electron asar-integrity fuse | S5 |
| 15 | Antigravity.exe as a tool for attackers | `ELECTRON_RUN_AS_NODE` turns our exe into a script runner | None in MVP | TMP-06 | ⚠️ Out of scope — next: disable fuses with `@electron/fuses` [STRETCH] | — |
| 16 | Install process | Tampered installer in transit | SHA-256 published with release; GitHub-hosted download | INS-02 | 🟡 Partial — real fix is code signing | — |
| 17 | Install process | Unsigned warning scares users / trains them to click through | Explicit, rehearsed SmartScreen handling; USB install for demo; signing listed as step 1 after event | INS-01 | 🟡 Accepted for demo | — |
| 18 | The owner's PC | Bundled extras, persistence, leftovers | Inventory allow-list; no services/tasks/Run keys; full-clean uninstaller | INS-03..05 | ✅ Mitigated | S1, S2 |
| 19 | The owner's PC | AV false positive blocks or flags us | No UPX, no encoded/hidden PowerShell, plain read-only script; Defender-on VM testing | INS-06, LP-07 | ✅ Mitigated (monitored) | S5 |
| 20 | Availability of the scan | GPO execution policy or Constrained Language Mode blocks collector | Clear error message; CLM detection recorded | §6.8 row 7 | 🟡 Partial — rare for no-IT SMMEs | — |

---

## §8 Programme-aware build timeline

### 8.1 Read this first: sources, conflicts and adjustments

**Sources.** The programme PDF and the Idea Canvas have **not** been available to the author of this manual — only the times quoted in the five prompts. Every programme time below comes from those prompts. Slots the prompts don't describe are marked *(confirm against programme)*. **Tshedi: before printing this section, check every row's left two columns against the official programme and fix any that differ.**

**Conflicts found and how this plan resolves them** — rather than papering over them:

| # | Conflict | Resolution in this plan |
|---|---|---|
| C1 | **Pre-written code vs "hacking only from 16:00".** The pre-travel brief asks each member to "confirm their brick builds from a clean checkout". If competition rules forbid code written before 16:00 Day 1, real brick code can't exist yet — and this manual itself contains a lot of code. | Pre-travel work is **toolchain proof only**: each member builds an empty scaffold (hello-world Electron window, `print("ok")` PyInstaller exe, one-line PowerShell script, blank Vite page) from a clean checkout, plus non-code prep (installs, caches, baseline version research, licence keypair, VM). **Shakir: email the organisers before travel** asking whether (a) design documents with code snippets and (b) pre-generated config/keys/data files are allowed. If the answer is strict, the repo at 16:00 contains only scaffolds, docs and data, and the manual's code is typed in during the event. |
| C2 | **Canvas "Day 1: working end-to-end scan" vs the clock.** Day 1 gives 16:00–18:00 + 19:00–21:00 = **4 hours of build time** before the end-to-end deadline. A *packaged* end-to-end in 4 hours is not realistic. | The 21:00 target is an end-to-end **dev-mode** scan producing an HTML report. The **installer** target moves to 00:00. If the canvas promises an installed product on Day 1 evening, it is over-promising — update the canvas wording to "dev-mode end-to-end on Day 1; installer by midnight". *(Check the canvas wording.)* |
| C3 | **"Bricks A+B+C snap together" at 19:00, but the spawn wiring is Brick D.** §4.5–§5.5 put `runProcess.ts`, `paths.ts` and the IPC handlers in Schwan's brick. Without them, A+B+C cannot run end to end. | Schwan's 16:00–18:00 skeleton **is** the main-process pipeline (paths, spawn, IPC) tested with stubs (§5.10). It merges at 19:00 with A, B and C. Packaging config (NSIS) comes later, at 21:15. |
| C4 | **§1.9 and §6 targeted integration 21:15–23:59; this section (per the programme brief) wants it 19:00–21:00.** | §8 wins. Integration (§6 Phases 1–3, 5) runs 19:00–21:00; installer (§6 Phases 4, 6) runs 21:15–00:00. Contract sign-off **and** freeze are both at **16:00**; later changes need all four members to agree (§0.10). |
| C5 | **§5.8 builds the final installer from a tag at 11:00 Day 2, but the 11:00 mentor checkpoint demos the installer.** You can't demo at 11:00 a build that starts at 11:00. | Release candidates (§8.7): RC1 built 06:45, verified 08:00–09:00, installed on the demo laptop. The checkpoint demos RC1. Any 10:30–11:00 fix becomes RC2 only if it passes the VM smoke test by **11:25**; otherwise RC1 is submitted. |
| C6 | **Day 2 07:00–09:00 "nobody codes" vs 08:00–09:00 "final clean-VM test".** | No contradiction if testing isn't coding: 07:00–08:00 is breakfast with laptops closed; 08:00–09:00 is testing and artefact capture with **no code changes**. Code changes are allowed again only 10:30–11:00. |
| C7 | **"2-day hackathon" vs actual coding time.** | Total hands-on-keyboard time is ~14.5 hours (§8.2), not two days. Plan scope accordingly — the MVP cut list stands, and nothing [STRETCH] is started before the 00:00 security pass is green. |

### 8.2 The real hacking budget

| Window | Hours | Usable for |
|---|---|---|
| Day 1 16:00–18:00 | 2.0 | Brick skeletons |
| Day 1 18:00–19:00 | 0 | Dinner — no coding |
| Day 1 19:00–21:00 | 2.0 | Integration (dev mode) |
| Day 1 21:00–21:15 | 0 | Mentor check-in |
| Day 1 21:15–06:00 | 8.75 (×4 people, minus 2 h sleep each) | Installer, hardening, security pass, bug fixes |
| Day 2 06:00–07:00 | 1.0 | Bug fixes only; RC1 |
| Day 2 07:00–10:30 | 0 code | Testing, artefacts, talks |
| Day 2 10:30–11:00 | 0.5 | Critical fixes only |
| **Total code time** | **≈ 14.25 h** | — |

### 8.3 Pre-travel plan and per-member estimates

**This is the single biggest schedule risk in the whole project.** If one person arrives without a working offline toolchain, they lose 16:00–19:00 fixing installs on venue Wi-Fi, their brick isn't ready at 19:00, and integration slips past the 21:00 mentor check-in. Every later row in this timeline depends on pre-travel being complete.

Deadlines (T = Day 1 departure):

| When | Milestone | Proof posted in team chat |
|---|---|---|
| **T−3 days** | §1.2 installs done on every laptop | Screenshot of the §1.1 `--version` checks |
| **T−2 days** | Offline test passes (§1.5): Wi-Fi off, delete `node_modules`, `npm ci --prefer-offline`, `npm run dev` opens; venv installs from wheelhouse | Screenshot with Wi-Fi icon off |
| **T−2 days** | Each member's scaffold builds from a **fresh clone** (C1) | Screenshot of the build output |
| **T−1 day** | Schwan's USB kit complete; clean VM checkpoint saved; Vercel placeholder live | USB file list; VM screenshot; URL |
| **T−1 day, 20:00** | Go/no-go call (15 min). Anyone not green gets a buddy for an evening session | Message: "Pre-travel: 4/4 green" |

Per-member estimates (honest; add 50% if a laptop is older than 4 years or has corporate restrictions):

| Member | Tasks (sections) | Realistic time | Main risk |
|---|---|---|---|
| **All** (each) | §1.2 steps 1–12 installs (1.5 h); npm caches for desktop + landing (0.5–1 h, mostly Electron download); Python wheelhouse (0.25 h); offline test (0.5 h); VS Code extensions (0.25 h); security tools download §7.2 (0.25 h) | **3.5–4.5 h** | Electron binary download fails on home connection → use `ELECTRON_MIRROR` (§1.6) |
| **Tshedi** (A) | All of the above + empty-package PyInstaller build verified in Windows Sandbox (§2.12, 1 h incl. enabling Sandbox + reboot); baseline research — 12 apps × ~10 min (§2.8, 2 h); ASR rule GUID shortlist with Shakir (0.5 h) | **7–8 h** | Baseline research is easy to under-estimate |
| **Shakir** (B) | All + licence keypair and 3 demo tokens + expired token (§3.11, 0.5 h); confirm the **⚠ verify** encodings on two machines (§3.5, 1.5–2 h — needs access to a second, differently configured PC); organisers' rules email (C1) | **6–7 h** | No second machine available → borrow one, or use Schwan's VM |
| **Frank** (C) | All + Tailwind/shadcn init in desktop and landing scaffolds (§1.2 steps 14–19, 1 h); Vercel project + placeholder deploy (§4.13 steps 1–6, 0.5–1 h); demo laptop chosen and charged | **5–6 h** | Vercel/GitHub permissions on a team repo |
| **Schwan** (D) | All + Windows 11 VM download (~6–20 GB) and setup with standard + admin users (§1.2 step 13, 3–4 h, mostly unattended); warm electron-builder caches by building the scaffold installer (§1.6, 1 h); USB recovery kit (§1.5, 1 h) | **9–11 h** (≈ 5 h hands-on) | VM download over slow home internet — **start it first, on day T−5** |

### 8.4 Day 1 timeline

Columns as specified. "Pass" = deliverable met; "Fallback" = what happens if not (see also the ladder in §8.8).

| Time slot | Programme activity | Team Antigravity action | Owner(s) | Output / artefact | Fallback if late |
|---|---|---|---|---|---|
| Before 15:30 | Arrival, registration, opening *(confirm against programme)* | Set up at one table: power strip, Schwan's USB kit, phone hotspot. Each member runs `node -v`, `py -3.12 --version`, `git status` — **no code**. Join venue Wi-Fi but plan as if it's absent | All | Four laptops ready; team chat open | Anyone failing a check restores from USB (§1.6 step 4) now, not at 16:00 |
| 15:30–16:00 | Challenge planning | Walk through §0 together (contract, output contract, `unavailable` vs `failed`). Make only blocking changes via a `contract/*` PR. Each owner says "I sign off on §0" aloud; Tshedi records it. **No coding before sign-off.** Assign the ticket board (§8.9) | Tshedi leads; all sign | Signed contract in `shared/contract/CHANGELOG.md` (`1.0.0`, four names, 16:00) | 16:00 hard stop: sign §0 **as written** (defaults stand); log open questions as tickets for dinner |
| 16:00–18:00 | Hacking begins | **Brick skeletons + first isolation test.** Tshedi: parser + 5 scorers returning fixed results + CLI writing `report.json` (§2.3, §2.11) → `pytest` on fixtures. Shakir: `collector.ps1` + `Common.ps1` + Host and Protection probes, `-DryRun` (§3.2–§3.5) → `Test-ReadOnly.ps1`; `verify.ts` with tests (§3.11). Frank: 4 screens against `report.all-states.json` in mock mode (§4.9, §4.12) → `npm run test`. Schwan: `paths.ts`, `runProcess.ts`, `runCollector/Engine.ts`, IPC handlers, preload (§4.6–§5.5) → stub run (§5.10) | Each owner | **One brick each passing its own isolation test by 18:00**, pushed to its `brick/*` branch | At 17:30, any owner who won't make it says so; the brick integrates at 19:00 via **fixtures/stubs** (§8.8, rung 1) and keeps building in parallel |
| 18:00–19:00 | Dinner | **No coding.** Cross-review the contract: Tshedi reads Shakir's real `-DryRun` output; Frank reads Tshedi's first `report.json`; Schwan checks exit codes and arguments (§4.7) against §2.11 and §3.3. Any needed change → all four agree in the team channel, then one `contract/*` PR merged before 19:15 (§0.10) | All | Short list of contract tickets, each with owner | Changes that aren't blocking wait until after integration, and still need all four members to agree |
| 19:00–21:00 | Hacking | **First integration attempt — §6 Phases 1–3 and 5.** 19:00 force-push ban starts (§1.9). Merge order: contract → engine → collector → desktop UI → main pipeline (§6.2). Run the schema gate on real collector output (§6.3 step 2.3). Run the app in dev mode, real collector + engine from source (§6.6 steps 5.1–5.5). Tag `v0.1-integrated` | Tshedi merges; all | **End-to-end dev-mode scan producing `report.html`** (+ results screen) on Dev-1, tag `v0.1-integrated` | 20:30 checkpoint: if not working, cut per ladder rung 2 (PDF → screenshot), then rung 3 if still broken at 21:00 |
| 21:00–21:15 | Mentor check-in | **5-minute demo** of the dev-mode run: licence → scan → results → HTML report. Frank drives, Tshedi narrates. Shakir writes every mentor comment as a ticket, tagged `mentor` | Frank, Tshedi; Shakir scribes | Ticket list `mentor-d1-*` | If e2e broken: demo the mock-mode UI + a real `scan.json` + engine-generated HTML separately, state honestly what's left |
| 21:15–00:00 | Night shift begins | Schwan: `electron-builder.yml`, NSIS include, PyInstaller handoff, manifest script, `build-all.ps1` → first installer → install on one clean-ish machine (VM or a teammate's spare account) (§5.2–§5.9, §6.7). Frank: PDF layout spec handed to Tshedi; "Open PDF" wired; progress model (§4.8, §4.11). Tshedi: remaining scoring rules + boundaries, `pdf.py`, `test_integrity.py` (§2.5, §2.10, §7.6). Shakir: remaining probes, all mocks, `Test-Collector.ps1`, `-RunId` + `AG-PHASE` (§3.5–§3.10). 22:30 quick sync (5 min, standing) | Each owner | **Installer installed and scanning on one clean-ish machine by 00:00**; PDF opens from the app; tag `v0.2-installer` | 23:00 ladder rung 4 (installer not building → dev-mode demo + pre-recorded video). Schwan keeps going alone until 02:00; others continue their tasks |
| 00:00–02:00 | Overnight hacking + mentor support | **§7 first pass.** Shakir + Schwan on the VM: RO-01, RO-02, RO-03 (read-only diff, Procmon, audit log); LIC-01–LIC-07; PRV-01, PRV-02 (network capture, firewall block). Tshedi: RPT-01–RPT-06 (automated). Frank: RPT-07, RPT-08 (escaping, PDF/HTML/app agreement). Fixes for any ❌ go on `fix/*` branches with a ticket | Shakir leads | **Pass/fail sheet** `docs/security-results.md` with a ticket per ❌ | 01:00: any **critical** ❌ (a write by the collector, a tampered token accepted, any network call) → ladder rung 5: escalate to a mentor during this support window; never ship silently |
| 02:00–06:00 | Shower slots + continued work | **Staggered rest (§8.5).** Awake pair does **mechanical work only — no new features**: clean-VM install test (§5.9), report rendering checks against fixtures and a real scan, pitch slides skeleton. Fixes allowed only for tickets from the 00:00 security pass | Rota §8.5 | VM test log line in `docs/decisions.md`; rendering check notes; `docs/pitch-skeleton` (slide titles + screenshots) | If the VM install fails at 02:00–04:00, the awake pair documents the failure precisely; Schwan fixes on waking at 04:00 (ladder rung 6) |

### 8.5 Overnight rest rota

**Default:** the two people who will **present** sleep first, so the pitch voices are freshest; the two who own the night's mechanical work (VM and security re-runs) stay up first. *Presenters are assumed to be Frank (demo) and Tshedi (lead/narration) — adjust when §9 fixes the speaker roles.*

| Window | Awake (mechanical work only) | Asleep | Awake pair's tasks |
|---|---|---|---|
| **02:00–04:00** | **Schwan + Shakir** | Frank + Tshedi | Schwan: full clean-VM test §5.9 steps 1–21 on `v0.2-installer` (or newer fix build). Shakir: re-run any ❌ from the security sheet after fixes; report rendering checks of the real VM scan (HTML vs app vs PDF, RPT-08) |
| **04:00–06:00** | **Frank + Tshedi** | Schwan + Shakir | Frank: pitch slides skeleton (structure, screenshots from the VM run, no polish); report rendering checks on all fixtures in the packaged app. Tshedi: review open tickets, prioritise for 06:00, write the 06:00 fix list; update `docs/decisions.md` |

Rules:
1. Book programme shower slots inside your **own awake** window or immediately on waking — not during your teammates' handover.
2. Handover at 04:00 is 5 minutes, written in the team chat: what's verified, what's broken, what's next.
3. Nobody merges to `main` while half the team sleeps, except Tshedi-approved security fixes during 04:00–06:00.
4. Two hours is short. Phone alarms for both sleepers; awake pair checks they're up.

### 8.6 Day 2 timeline

| Time slot | Programme activity | Team Antigravity action | Owner(s) | Output / artefact | Fallback if late |
|---|---|---|---|---|---|
| 06:00–07:00 | End of night shift *(confirm what the programme lists here)* | **Code freeze on new features — bug fixes only.** 06:00 stand-up (5 min): Tshedi reads the fix list. Fix only tickets marked `security-critical` or `demo-blocking`. **06:45: build RC1** (`build-all.ps1`, §5.8) and tag `v1.0.0-rc1` | Tshedi (merges); owners fix; Schwan builds | `Antigravity-Setup-1.0.0-rc1.exe` + `SHA256SUMS.txt` | If RC1 build fails at 06:45, fall back to the newest installer that passed a VM test overnight; record which |
| 07:00–08:00 | Breakfast | **Nobody codes. Laptops closed.** Talk through the demo story informally | All | — | — |
| 08:00–09:00 | *(confirm: still breakfast/reset block per programme)* | **No code changes.** Schwan: RC1 clean-VM test §5.9 steps 1–21. Shakir: final §7 pass on RC1 — RO-01..03, LIC-08, PRV-01, PRV-04, LP-02..05, TMP-01..04, INS-03..06; update the sheet. Frank: produce **fallback artefacts** — 2–3 min screen recording of a full scan on the VM, saved `report.html` + `action-plan.pdf` from that run, screenshot deck (licence, scanning, results, PDF). Tshedi: install RC1 on the **demo laptop from USB** (§5.7), run one scan; draft submission text | As listed | RC1 verified; `docs/security-results.md` final; `fallback/scan-demo.mp4`, `fallback/report.html`, `fallback/action-plan.pdf`, `fallback/screens.pdf`; demo laptop ready | If RC1 fails the VM test: the failure becomes a 10:30 ticket; demo laptop keeps the last good build; fallback artefacts are recorded from whichever build works |
| 09:00–09:45 | Talk: **SMME cybersecurity (directly on-topic)** | **Frank + Tshedi attend** (pitch owners). Take notes on: the language speakers use for SMME risk, any South African statistics, POPIA framing, what they say owners actually do. Feed 1–2 points into the pitch | Frank, Tshedi | 5 bullet notes in `docs/pitch-notes.md` | If the slot clashes with a blocker, at least **one** of them attends |
| 09:45–10:00 | Speaker session | **Shakir attends**; Schwan stays with the demo laptop (charging, updates paused) | Shakir | Notes if relevant | — |
| 10:00–10:30 | Speaker session | **Schwan attends**; Shakir prepares the submission bundle folder | Schwan | Notes if relevant | — |
| 10:30–11:00 | Final hacking | **Bug fixes only, driven by the security test sheet** and RC1 VM results. Admit a fix only if it is `security-critical` or `demo-blocking` **and** fits in 15 minutes. At **10:55**: if anything merged, Schwan starts RC2 build; otherwise RC1 is final | Owners; Tshedi approves | Either "RC1 final" or RC2 building | Any fix not merged by 10:50 is dropped and disclosed in the submission notes |
| 11:00–11:15 | Mentor checkpoint | **5-minute installer end-to-end demo** on the demo laptop (RC1): open installer → (SmartScreen narration) → licence → scan → results → PDF. Shakir logs feedback. Meanwhile Schwan runs RC2 VM smoke test (§5.9 steps 1–14) if RC2 exists | Frank drives, Tshedi narrates; Schwan on VM | Mentor notes; RC2 smoke result | If the laptop misbehaves: play `fallback/scan-demo.mp4` and open the saved PDF |
| 11:15–11:45 | Submission prep | **Submit by 11:30. The buffer to 11:45 is non-negotiable.** 11:15 decide RC1 vs RC2 (§8.7). 11:20 tag `v1.0.0-demo` on the chosen commit; GitHub Release with installer + `SHA256SUMS.txt` (§5.8 step 9); Frank updates the landing download link. Submit: installer link, repo link at the tag, sample report (`report.html` + `action-plan.pdf` from the VM), security test sheet (`docs/security-results.md`) | Shakir submits; Schwan release; Frank landing | **Submission confirmation screenshot by 11:30** | 11:25: if the GitHub Release isn't up, submit the installer through whatever upload the submission form accepts, or a team Google Drive link. Never wait past 11:30 for polish |
| 11:45–12:30 | *(confirm against programme — likely lunch)* | Eat. Optional 20-minute rest for the presenters | All | — | — |
| 12:30–13:00 | Pitch prep | **Rehearse the demo script twice** (§9), with a timer, on the demo laptop, including the fallback switch (video + saved PDF) | All | Two timed runs, both under the limit | If the second run overruns, cut the slide-only parts, never the live scan |
| 13:00–14:10 | Pitches | Present per §9. Demo laptop on charge until called | All | — | Fallback artefacts open in a second window, ready |

### 8.7 Release-candidate rule for Day 2

| Build | When built | Verified by | Used for |
|---|---|---|---|
| `v0.2-installer` | Day 1 by 00:00 | Install on one clean-ish machine | Overnight security pass, VM test |
| `v1.0.0-rc1` | Day 2 06:45 | Full §5.9 + final §7 pass, 08:00–09:00 | Demo laptop; 11:00 checkpoint; default submission |
| `v1.0.0-rc2` | Day 2 10:55, only if a 10:30–11:00 fix merged | §5.9 steps 1–14 on VM, 11:00–11:20 | Submitted **only if** smoke test passes by 11:25 |
| `v1.0.0-demo` | Tag placed at 11:20 on whichever of RC1/RC2 is submitted | — | Submission and pitch |

The demo laptop is **not** updated to RC2 before the pitch unless RC2 fixes a bug that would show in the demo.

### 8.8 "If we are behind at T, we cut X" ladder

The MVP is fixed (§0, Prompt 1): **licence key entry → scan < 60 s → HTML report with 5 categories (status, evidence, explanation) → one-page PDF with top 3 fixes.** Already cut: live CVE lookups, auto-remediation, cloud backup integrations, non-Windows, scan history. *(Confirm against the Idea Canvas's MVP cut list; if it lists more cuts, add them to rung 0.)*

Cuts happen **in this order** — never skip a rung to cut something more visible.

| Rung | Check at | Condition | Cut / action | Keeps the MVP? | Decided by |
|---|---|---|---|---|---|
| 0 | Any time | Someone starts a [STRETCH] item before the 00:00 security pass is green | Stop it. [STRETCH] items (restart-as-admin, dark mode, exposed risk score, fuses, CLM handling, pktmon) are cut by default | Yes | Tshedi |
| 1 | **Day 1 18:00** | A brick fails its isolation test | Integrate with **fixtures/stubs** in its place (collector → `collector-stub.ps1` emitting a fixture; engine → canned `report.json`); owner keeps building on their branch. Reduce scope inside the brick: software baseline to 5 entries; ASR to "count of rules in block"; backup to File History + agents only | Yes, if the real brick lands by 21:15 | Tshedi + owner |
| 2 | **Day 1 21:00** | End-to-end dev-mode scan doesn't work | **Cut PDF export to a screenshot** of the HTML report's top-3 section for the demo; HTML report remains the deliverable. Progress bar becomes an indeterminate spinner | MVP PDF **at risk** — restore by 00:00 or keep the cut | Tshedi |
| 3 | **Day 1 21:15** | Still no real end-to-end | Demo at check-in with parts shown separately (§8.4 fallback). Freeze all non-integration work until end-to-end works; everyone pairs on the failing joint | Not yet | Tshedi |
| 4 | **Day 1 23:00** | Installer isn't building | **Demo in dev mode with a pre-recorded video** of a full scan as backup. Schwan alone continues installer work until 02:00; everyone else returns to their tasks | Installer **at risk** | Tshedi + Schwan |
| 5 | **Day 1 00:00–01:00** | §7 first pass fails a **critical** item: any write by the collector/engine (RO-01..03), tampered/expired token accepted (LIC-02..06), any network call (PRV-01), or personal data in output (PRV-04) | **Escalate to a mentor** in the 00:00–02:00 support window. Fixing it outranks every remaining feature. If it can't be fixed by 06:00: remove the claim from the pitch, state the limitation in the submission notes. **Never ship silently** | Yes, honestly | Shakir raises; Tshedi decides |
| 6 | **Day 2 04:00** | Installer still fails on the clean VM | Prepare a **portable zip** of `release\win-unpacked` + one-page run instructions as the submission fallback; keep fixing until 06:45 | Partly (no installer) | Tshedi + Schwan |
| 7 | **Day 2 06:00** | Anything unfinished | Code freeze: unfinished items are cut, not squeezed in. Candidates in order: progress phase messages → admin hint → landing-page polish → Windows 10 overlay explanation → ASR detail rows. **Never cut:** licence check, any of the 5 categories, evidence rows, read-only guarantee | Yes | Tshedi |
| 8 | **Day 2 09:00** | RC1 fails the final VM test | Submit the newest overnight build that passed; RC1 failure becomes a 10:30 ticket | Yes | Tshedi |
| 9 | **Day 2 11:15** | RC2 not verified | Submit RC1 | Yes | Tshedi |
| 10 | **Day 2 11:30** | Anything at all | **Submit what you have.** Submission notes list known issues honestly | — | Shakir submits |

### 8.9 Decision rights and ticket handling

| Topic | Rule |
|---|---|
| Who calls a cut | Tshedi (lead). If Tshedi is asleep (02:00–04:00), Shakir decides; Tshedi reviews at 04:00 |
| Where tickets live | **Default:** GitHub Issues with labels `brick:A/B/C/D`, `mentor`, `security-critical`, `demo-blocking`, `stretch`. Rationale: they link to PRs and work offline-ish via the phone hotspot; fallback is a shared text file in the repo, `docs/tickets.md` |
| Mentor feedback | Logged as tickets within 5 minutes of the check-in; Tshedi triages at the next sync |
| Syncs | 16:00 (start), 17:30 (risk call), 19:00 (merge), 20:30 (e2e check), 21:15 (post-mentor triage), 22:30, 00:00 (security pass start), 01:00 (critical-fail call), 04:00 (handover), 06:00 (freeze), 10:30, 11:15. Each ≤ 5 minutes, standing |
| Decisions log | Every cut, rung hit, and RC choice → one line in `docs/decisions.md` with time and name |

---

## §9 Demo rehearsal & fallback

### 9.1 Roles

| Role | Person | Responsibility during the slot |
|---|---|---|
| **Lead presenter** | Tshedi | Opens the pitch, narrates the demo, closes with the ask |
| **Driver** | Frank | Only person touching the demo laptop. Silent except for one line in the demo |
| **Security voice** | Shakir | 40-second "why it's secure" proof; leads security questions in Q&A |
| **Timekeeper + fallback operator** | Schwan | Watches the clock (phone stopwatch), shows cue cards, calls "switch", holds the backup laptop and USB. Speaks only in Q&A (packaging/install questions) |

These match the rest assumptions in §8.5. If the team changes presenters, update §8.5 at the 08:00 Day 2 re-baseline (maintenance note).

### 9.2 Slot assumptions

The programme gives **13:00–14:10 for all pitches**. Our team's individual slot time and length are not yet known *(confirm with organisers on Day 2 morning)*. The script below uses the run sheet you specified — 5 minutes pitch, 5 minutes demo, then Q&A — and writes times as **13:00-based clock times**. If our slot starts at, say, 13:33, add 33 minutes to every time; Schwan writes the real times on the cue cards at 12:30.

If the organisers give **less than 10 minutes** in total, cut the pitch slides to 3 minutes; never cut the live scan.

### 9.3 Demo laptop layout

Prepared during the pre-pitch checklist (§9.7). Windows open, in this Alt+Tab order:

| # | Window | State |
|---|---|---|
| 1 | Slides (PDF or PowerPoint, full screen) | On slide 1 |
| 2 | **Antigravity** app | On the **License screen** (reset with `reset-demo.ps1`, §9.6) |
| 3 | `scan-demo-results.mp4` in the Media Player / Films & TV app | Paused at 0:00, **muted** |
| 4 | `action-plan.pdf` (fallback copy) in Edge | Open, page 1 |
| 5 | `screens.pdf` (screenshot deck) in Edge | Open, page 1 |

Taskbar: Wi-Fi icon visible showing **disconnected / airplane mode** — it is part of the story.

### 9.4 The 5-minute demo script

Lines are suggested wording; say them in your own words, but keep the order and the timing. **Bold** times are hard checkpoints Schwan calls.

**Pitch (13:00–13:05)** — slides only; outline here so the demo connects to it.

| Clock | Speaker | Content | Screen |
|---|---|---|---|
| 13:00:00 | Tshedi | Problem: South African small businesses (5–50 staff, no IT person) get hit by ransomware and find out too late that backups or protections weren't there. *(Add one point from the 09:00 SMME talk, §8.6.)* | Slide 1–2 |
| 13:01:30 | Tshedi | What we built: a read-only Windows check that gives an owner-manager a red/amber/green answer and their top 3 fixes in about a minute | Slide 3 |
| 13:02:30 | Tshedi | The five checks in one line each | Slide 4 |
| 13:03:30 | Shakir | Why it's secure in 3 bullets (Idea Canvas "Why it's secure" wording, §7.10 S1–S5) | Slide 5 |
| 13:04:30 | Tshedi | "Let's show you. This laptop is offline — Wi-Fi is off." | Slide 6 "Live demo" |

**Demo (13:05–13:10)**

| Clock | Speaker | Says | Screen | Frank does |
|---|---|---|---|---|
| **13:05:00** | Tshedi | "Imagine this is the front-desk PC at a 12-person accounting firm." | App — License screen | Alt+Tab to the app; point at the Wi-Fi icon |
| 13:05:15 | Tshedi | "Each customer gets a signed licence key. It's checked right here on the PC — no server." | License screen | Ctrl+V the demo key (already in clipboard), click **Activate** |
| 13:05:30 | — | — | Main screen | Click **Start scan**; Schwan starts the **90-second scan timer** |
| 13:05:35 | Tshedi | "It's reading settings only — backups, Windows updates, outdated software, ransomware protections and recovery options. It never changes anything." | Scanning screen with progress messages | Hands off the keyboard |
| 13:06:00 | Shakir | "And nothing leaves this machine. We've proved that with packet and process monitoring — I'll come back to it." | Scanning | — |
| ~13:06:15 | Tshedi | "And there's the answer." | **Results** | — |
| 13:06:20 | Tshedi | "Overall red. The owner doesn't need to understand BitLocker or ASR — they see three fixes, in order, with how long each takes." | Results — top fixes | Scroll so the 3 fix cards are visible |
| 13:06:50 | Tshedi | "Every rating shows its evidence. Here, Defender real-time protection is off — that's why this is red." | Ransomware protections card | Click / scroll to that card; hover the evidence table |
| 13:07:20 | Frank | "And this is the one page the owner prints and sticks next to the PC." | PDF one-pager | Click **Open one-page action plan (PDF)** |
| **13:08:00** | — | **Fallback window closes** (§9.5) | — | — |
| 13:08:00 | Shakir | "Three things we tested, not just claimed: a before-and-after snapshot of the whole system shows the scan changes nothing; with all network blocked it runs identically; tampered or expired licence keys are rejected. The test sheet is in our submission." | PDF still on screen, or `security-results` slide | Alt+Tab to slide 7 when Shakir starts |
| 13:09:00 | Tshedi | Close: who it's for, what's next (signed installer, pilot with 5 local SMMEs), the ask | Slide 8 | — |
| **13:10:00** | Tshedi | "Thank you — questions?" | Slide 8 | — |

Demo scenario note: the demo laptop should show **at least one red and one amber** so the story works. **Default:** turn Defender real-time protection off on the demo laptop at 12:40 (Tamper Protection off first), and back on straight after the pitch. Rationale: a real, explainable red finding is more convincing than an all-green PC. Never do this on a judge's or venue machine.

### 9.5 Fallback triggers

Schwan watches the clock and calls "**switch**" out loud. Frank reacts; nobody debugs on stage.

| ID | Trigger (exact) | Action | Who says what |
|---|---|---|---|
| F1 | **Scan has not produced the Results screen 90 seconds after clicking Start scan** (≈ 13:07:00) | Frank: Alt+Tab to window 3, press Play on `scan-demo-results.mp4` (40 s, results → PDF) | Tshedi: "This one's taking its time — here's the same scan we recorded on a clean machine this morning." Narrate the video using the same lines from 13:06:15 |
| F2 | App won't launch, crashes, or licence screen errors **twice** | Skip to `scan-demo-full.mp4` (75 s, launch → PDF), play from the start | Tshedi: same line as F1 |
| F3 | Demo laptop or display output fails | Schwan's backup laptop: open `screens.pdf` (screenshot deck) full screen; or plug the USB into the venue PC and open `screens.pdf` | Tshedi talks through screenshots at the same pace |
| F4 | Nothing will display | Hand out the **3 printed copies** of `action-plan.pdf` to the judges; Tshedi describes the flow | — |
| **Window closes 13:08:00** | If the live app still isn't on Results at 13:08 (even mid-F1), **stop the demo**; show `action-plan.pdf` (window 4) and go to Shakir's segment on time | Tshedi: "Here's the output it produces." |

Rules: one fallback switch per pitch — never switch back to the live app. Schwan shows cue cards: **"2:00 left"** at 13:08:00, **"WRAP"** at 13:09:30.

### 9.6 Fallback artefacts: where they live and how to launch them

Produced 08:00–09:00 Day 2 from the verified RC1 run on the clean VM (§8.6). Three copies: demo laptop, Schwan's backup laptop, USB.

| Artefact | Demo laptop path | USB path | Made with | Launch |
|---|---|---|---|---|
| Full scan recording (75 s) | `C:\AG-Demo\fallback\scan-demo-full.mp4` | `E:\AG-Demo\fallback\…` | Windows Snipping Tool → Record (Win 11) or Game Bar `Win+Alt+R` — built in, offline | Shortcut **"2 VIDEO FULL"** on desktop, or `Start-Process C:\AG-Demo\fallback\scan-demo-full.mp4` |
| Results-only clip (40 s) | `C:\AG-Demo\fallback\scan-demo-results.mp4` | same | Trimmed from the full video in Clipchamp or Photos (offline trim) | Pre-opened (window 3); shortcut **"1 VIDEO RESULTS"** |
| Saved HTML report | `C:\AG-Demo\fallback\report.html` | same | Copied from `%LOCALAPPDATA%\Antigravity\runs\<id>\` on the VM | `Start-Process C:\AG-Demo\fallback\report.html` |
| Saved PDF one-pager | `C:\AG-Demo\fallback\action-plan.pdf` | same | As above | Pre-opened (window 4); shortcut **"3 PDF"** |
| Screenshot deck | `C:\AG-Demo\fallback\screens.pdf` | same | 5 screenshots (licence, scanning, results top, evidence card, PDF) pasted into a slide file, exported to PDF | Pre-opened (window 5); shortcut **"4 SCREENS"** |
| Final installer + checksum | `C:\AG-Demo\Antigravity-Setup-1.0.0.exe`, `SHA256SUMS.txt` | `E:\AG-Demo\` | §5.8 | Only if a judge asks to see install |
| Demo licence key | `C:\AG-Demo\demo-key.txt` | `E:\AG-Demo\demo-key.txt` | §3.11 | Loaded into clipboard by `reset-demo.ps1` |
| Printed PDF | 3 paper copies of `action-plan.pdf` | — | Venue printer or printed before travel from a fixture run | Hand out (F4) |

Demo reset script (in the repo as `docs/demo/reset-demo.ps1`; copied to `C:\AG-Demo\`). Run it at 12:50 and again just before walking up:

```powershell
# C:\AG-Demo\reset-demo.ps1   — cwd: C:\AG-Demo
Remove-Item "$env:APPDATA\Antigravity\license.txt" -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Antigravity\runs\*" -Recurse -Force -ErrorAction SilentlyContinue
Get-Content "$PSScriptRoot\demo-key.txt" -Raw | Set-Clipboard
Write-Host "Reset done. Key in clipboard. Now open Antigravity." -ForegroundColor Green
```

```powershell
# cwd: C:\AG-Demo
powershell -NoProfile -ExecutionPolicy Bypass -File .\reset-demo.ps1
```

Only the demo laptop runs this. It removes the app's own files only (licence and the last run), never system settings.

### 9.7 Pre-pitch checklist

Run 12:30–12:55 (§8.6). Schwan reads each line aloud; the owner answers "done".

| # | Item | Owner | Done |
|---|---|---|---|
| 1 | **Demo laptop charged to 100%** and on its charger until called | Frank | ☐ |
| 2 | **Backup laptop charged** (Schwan's), with all fallback artefacts and the clean VM | Schwan | ☐ |
| 3 | **Clean VM** on the backup laptop reverted to `clean-baseline`; installer copied in; ready if a judge asks for a fresh install | Schwan | ☐ |
| 4 | **Final installer + `SHA256SUMS.txt` on USB**; USB also has the whole `AG-Demo` folder | Schwan | ☐ |
| 5 | **Network OFF** on the demo laptop: airplane mode on, Wi-Fi and Bluetooth off; icon visible in taskbar | Frank | ☐ |
| 6 | **Demo licence key pre-loaded**: `reset-demo.ps1` run → app on License screen, key in clipboard; `demo-key.txt` open in Notepad as a backup | Frank | ☐ |
| 7 | One full rehearsal scan at 12:45 succeeded on this laptop in < 60 s; then reset (item 6) | Frank | ☐ |
| 8 | Demo scenario set: Defender real-time protection **off** (Tamper Protection off first) for a red finding (§9.4 note); reminder note to turn back on afterwards | Shakir | ☐ |
| 9 | **Do not disturb / Focus** on; all notifications off; Windows Update paused; screensaver and sleep off (Settings → Power → Never) | Frank | ☐ |
| 10 | All other apps closed; windows open in the §9.3 order | Frank | ☐ |
| 11 | Display: tested on the venue projector or HDMI earlier; scaling 125% or as tested; mirror (not extend) | Frank | ☐ |
| 12 | **Adapters**: HDMI cable, USB-C → HDMI, USB-C → USB-A, power strip; spare of the one we actually use | Schwan | ☐ |
| 13 | Media player muted; video paused at 0:00 | Frank | ☐ |
| 14 | Edge has opened `report.html` and `action-plan.pdf` once offline (no first-run prompts) | Frank | ☐ |
| 15 | **Timekeeper ready**: Schwan has phone stopwatch, cue cards ("2:00 left", "SWITCH", "WRAP") with real clock times written in | Schwan | ☐ |
| 16 | 3 printed copies of `action-plan.pdf` in Tshedi's hand | Tshedi | ☐ |
| 17 | Submission confirmation screenshot on Shakir's phone (in case judges ask) | Shakir | ☐ |
| 18 | Water; phones on silent | All | ☐ |

After the pitch: turn Defender real-time protection and Tamper Protection back **on**, re-enable Wi-Fi, resume Windows Update (Shakir checks).

### 9.8 Q&A preparation

| Likely question | Who answers | Short honest answer |
|---|---|---|
| "Why is the installer unsigned / why did SmartScreen appear?" | Schwan | A trusted signing certificate takes days to issue; signing is the first post-event step. We publish a SHA-256 checksum meanwhile (§5.7, §7.9) |
| "Can someone bypass the licence?" | Shakir | Forged and edited keys are rejected (signature check). A determined person could patch the app or roll the clock back — offline licensing can't prevent that; for a free local tool that's acceptable (§7.10 row 9) |
| "How do you know it's read-only?" | Shakir | Code is limited to an allow-list of read commands, checked automatically; we diffed full system snapshots before/after and watched every file and registry write with Process Monitor — zero writes outside our own report folder (§7.3) |
| "What data do you collect? POPIA?" | Shakir | System settings only: versions, on/off states, dates. No names, files, emails, IP addresses. Nothing is uploaded; uninstall deletes everything (§7.5) |
| "What if the PC uses another antivirus?" | Tshedi | We detect it through Windows Security Center and don't penalise the PC for Defender being passive (§2.5.4) |
| "Why not just use Microsoft Secure Score / Defender?" | Tshedi | Those need Microsoft 365 business licensing and an IT person to read them. We give a non-technical owner three plain-English fixes on one page |
| "How accurate is the patch check?" | Tshedi | It's a heuristic: newest installed update older than 30 days = amber, 60 = red. It can't see every update type; we say so in the report |
| "What's next?" | Tshedi | Signed installer, pilot with local SMMEs, multi-PC summary for a whole office *(align with Idea Canvas roadmap)* |
| "Does it need admin rights?" | Schwan | No. It installs and runs as a normal user; running as administrator just fills in a few more checks (§7.7) |

### 9.9 Pitch-slot run sheet (one page)

> Times assume our slot starts at 13:00. **Schwan writes the real times in the right-hand column at 12:30.**

| Clock (13:00 base) | What happens | Who | Screen | Real time |
|---|---|---|---|---|
| 12:30 | Pre-pitch checklist starts (§9.7) | Schwan reads | — | |
| 12:45 | Rehearsal scan on demo laptop, then reset | Frank | App | |
| 12:50 | Run `reset-demo.ps1`; windows in §9.3 order | Frank | — | |
| 12:55 | Walk to the stage area; demo laptop on charge | All | Slide 1 | |
| **13:00** | **Pitch start** — problem, solution, five checks | Tshedi | Slides 1–4 | |
| 13:03:30 | Why it's secure | Shakir | Slide 5 | |
| 13:04:30 | "This laptop is offline" | Tshedi | Slide 6 | |
| **13:05** | **Demo start** — licence → scan (start 90-s timer) | Frank drives, Tshedi narrates | App | |
| 13:06:15 | Results — overall, top 3 fixes, evidence | Tshedi | App | |
| 13:07:00 | **F1 trigger point** if no results yet → results video | Schwan calls | Video | |
| 13:07:20 | PDF one-pager | Frank | PDF | |
| **13:08** | **Fallback window closes** — no more switching; "2:00 left" card | Schwan | — | |
| 13:08:00 | Security proof | Shakir | Slide 7 | |
| 13:09:00 | Close and ask | Tshedi | Slide 8 | |
| 13:09:30 | "WRAP" card | Schwan | — | |
| **13:10** | **Q&A** | Tshedi routes; owners answer (§9.8) | Slide 8 | |
| After slot | Defender back on, Wi-Fi on, Update resumed | Shakir | — | |

---

## §10 Appendices

### Appendix A — Shared JSON schemas

Both files live in `/shared/contract/` (§0.5, §0.8) and are the machine-readable form of §0.6 and §0.8. JSON Schema draft 2020-12. Extra properties are **allowed** (forward compatibility, §0.6); PRV-05 (§7.5) checks for unexpected fields manually.

#### A.1 `shared/contract/scan.schema.json` — collector output → engine input

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://antigravity.local/contract/scan.schema.json",
  "title": "Antigravity collector output (scan.json)",
  "type": "object",
  "required": ["schema_version", "run_id", "collected_at", "collector_version", "duration_ms",
               "host", "backup", "patch", "software", "protection", "recovery"],
  "properties": {
    "schema_version":    { "type": "string", "pattern": "^1\\.\\d+\\.\\d+$" },
    "run_id":            { "$ref": "#/$defs/runId" },
    "collected_at":      { "$ref": "#/$defs/isoUtc" },
    "collector_version": { "type": "string", "minLength": 1 },
    "duration_ms":       { "type": "integer", "minimum": 0 },

    "host": {
      "type": "object",
      "required": ["hostname_hash", "os_caption", "os_build", "os_edition", "is_admin", "ps_version"],
      "properties": {
        "hostname_hash": { "type": "string", "pattern": "^sha256:[0-9a-f]+$" },
        "os_caption":    { "type": "string" },
        "os_build":      { "type": "string", "pattern": "^\\d+$" },
        "os_edition":    { "type": "string" },
        "is_admin":      { "type": "boolean" },
        "ps_version":    { "type": "string" }
      }
    },

    "backup": {
      "allOf": [{ "$ref": "#/$defs/section" }],
      "required": ["file_history_enabled", "file_history_last_backup", "windows_backup_last_success",
                   "onedrive_kfm_folders", "shadow_copy_count", "third_party_agents"],
      "properties": {
        "file_history_enabled":        { "type": ["boolean", "null"] },
        "file_history_last_backup":    { "$ref": "#/$defs/isoUtcOrNull" },
        "windows_backup_last_success": { "$ref": "#/$defs/isoUtcOrNull" },
        "onedrive_kfm_folders":        { "type": "array", "items": { "enum": ["Desktop", "Documents", "Pictures"] }, "uniqueItems": true },
        "shadow_copy_count":           { "type": ["integer", "null"], "minimum": 0 },
        "third_party_agents":          { "type": "array", "items": { "type": "string" } }
      }
    },

    "patch": {
      "allOf": [{ "$ref": "#/$defs/section" }],
      "required": ["hotfix_count", "latest_hotfix_installed_on", "days_since_latest_hotfix", "hotfixes", "pending_reboot"],
      "properties": {
        "hotfix_count":               { "type": ["integer", "null"], "minimum": 0 },
        "latest_hotfix_installed_on": { "$ref": "#/$defs/dateOrNull" },
        "days_since_latest_hotfix":   { "type": ["integer", "null"] },
        "hotfixes": {
          "type": "array", "maxItems": 10,
          "items": {
            "type": "object", "required": ["kb", "installed_on"],
            "properties": {
              "kb":           { "type": "string", "pattern": "^KB\\d+$" },
              "installed_on": { "$ref": "#/$defs/date" }
            }
          }
        },
        "pending_reboot": { "type": ["boolean", "null"] }
      }
    },

    "software": {
      "allOf": [{ "$ref": "#/$defs/section" }],
      "required": ["installed"],
      "properties": {
        "installed": {
          "type": "array", "maxItems": 500,
          "items": {
            "type": "object", "required": ["name", "version", "publisher"],
            "properties": {
              "name":      { "type": "string", "minLength": 1, "maxLength": 256 },
              "version":   { "type": "string", "maxLength": 64 },
              "publisher": { "type": "string", "maxLength": 256 }
            }
          }
        }
      }
    },

    "protection": {
      "type": "object",
      "required": ["bitlocker", "defender", "cfa", "asr"],
      "properties": {
        "bitlocker": {
          "allOf": [{ "$ref": "#/$defs/section" }],
          "required": ["os_volume_protection", "os_volume_encryption_pct"],
          "properties": {
            "os_volume_protection":     { "enum": ["on", "off", null] },
            "os_volume_encryption_pct": { "type": ["integer", "null"], "minimum": 0, "maximum": 100 },
            "encryption_method":        { "type": ["string", "null"] }
          }
        },
        "defender": {
          "allOf": [{ "$ref": "#/$defs/section" }],
          "required": ["antivirus_enabled", "realtime_enabled", "tamper_protected", "signature_age_days"],
          "properties": {
            "antivirus_enabled":  { "type": ["boolean", "null"] },
            "realtime_enabled":   { "type": ["boolean", "null"] },
            "tamper_protected":   { "type": ["boolean", "null"] },
            "signature_age_days": { "type": ["integer", "null"], "minimum": 0 },
            "third_party_av":     { "type": ["string", "null"] }
          }
        },
        "cfa": {
          "allOf": [{ "$ref": "#/$defs/section" }],
          "required": ["mode"],
          "properties": { "mode": { "enum": ["enabled", "disabled", "audit", null] } }
        },
        "asr": {
          "allOf": [{ "$ref": "#/$defs/section" }],
          "required": ["rules"],
          "properties": {
            "rules": {
              "type": "array",
              "items": {
                "type": "object", "required": ["id", "action"],
                "properties": {
                  "id":     { "type": "string", "pattern": "^[0-9a-fA-F-]{36}$" },
                  "action": { "enum": ["block", "audit", "warn", "off"] }
                }
              }
            }
          }
        }
      }
    },

    "recovery": {
      "allOf": [{ "$ref": "#/$defs/section" }],
      "required": ["winre_enabled", "system_restore_enabled", "restore_point_count", "latest_restore_point"],
      "properties": {
        "winre_enabled":          { "type": ["boolean", "null"] },
        "system_restore_enabled": { "type": ["boolean", "null"] },
        "restore_point_count":    { "type": ["integer", "null"], "minimum": 0 },
        "latest_restore_point":   { "$ref": "#/$defs/isoUtcOrNull" }
      }
    }
  },

  "$defs": {
    "runId":        { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}-\\d{2}-\\d{2}Z_[0-9a-f]{4}$" },
    "isoUtc":       { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$" },
    "isoUtcOrNull": { "anyOf": [{ "$ref": "#/$defs/isoUtc" }, { "type": "null" }] },
    "date":         { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
    "dateOrNull":   { "anyOf": [{ "$ref": "#/$defs/date" }, { "type": "null" }] },
    "section": {
      "type": "object",
      "required": ["status", "error"],
      "properties": {
        "status": { "enum": ["ok", "unavailable", "failed"] },
        "error":  { "type": ["string", "null"], "maxLength": 200 }
      }
    }
  }
}
```

#### A.2 `shared/contract/report.schema.json` — engine output → UI, HTML, PDF

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://antigravity.local/contract/report.schema.json",
  "title": "Antigravity engine output (report.json)",
  "type": "object",
  "required": ["schema_version", "run_id", "generated_at", "engine_version", "baseline_version",
               "overall", "summary", "categories", "fixes", "top_fixes", "scan"],
  "properties": {
    "schema_version":   { "type": "string", "pattern": "^1\\.\\d+\\.\\d+$" },
    "run_id":           { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}-\\d{2}-\\d{2}Z_[0-9a-f]{4}$" },
    "generated_at":     { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$" },
    "engine_version":   { "type": "string" },
    "baseline_version": { "type": "string" },
    "overall":          { "$ref": "#/$defs/rag" },
    "summary":          { "type": "string", "minLength": 1, "maxLength": 200 },

    "categories": {
      "type": "array",
      "minItems": 5, "maxItems": 5,
      "prefixItems": [
        { "$ref": "#/$defs/category", "properties": { "id": { "const": "backup" } } },
        { "$ref": "#/$defs/category", "properties": { "id": { "const": "patch" } } },
        { "$ref": "#/$defs/category", "properties": { "id": { "const": "software" } } },
        { "$ref": "#/$defs/category", "properties": { "id": { "const": "protection" } } },
        { "$ref": "#/$defs/category", "properties": { "id": { "const": "recovery" } } }
      ],
      "items": false
    },

    "fixes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "category", "severity", "title", "why", "steps", "effort_minutes", "needs_admin"],
        "properties": {
          "id":             { "$ref": "#/$defs/fixId" },
          "category":       { "$ref": "#/$defs/categoryId" },
          "severity":       { "enum": ["red", "amber"] },
          "title":          { "type": "string", "maxLength": 80 },
          "why":            { "type": "string", "maxLength": 160 },
          "steps":          { "type": "array", "minItems": 1, "maxItems": 5, "items": { "type": "string", "maxLength": 160 } },
          "effort_minutes": { "type": "integer", "minimum": 1 },
          "needs_admin":    { "type": "boolean" }
        }
      }
    },

    "top_fixes": { "type": "array", "maxItems": 3, "uniqueItems": true, "items": { "$ref": "#/$defs/fixId" } },

    "scan": {
      "type": "object",
      "required": ["is_admin", "duration_ms", "os_caption"],
      "properties": {
        "is_admin":    { "type": "boolean" },
        "duration_ms": { "type": "integer", "minimum": 0 },
        "os_caption":  { "type": "string" }
      }
    }
  },

  "$defs": {
    "rag":        { "enum": ["red", "amber", "green"] },
    "status":     { "enum": ["red", "amber", "green", "unavailable", "failed"] },
    "categoryId": { "enum": ["backup", "patch", "software", "protection", "recovery"] },
    "fixId":      { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
    "category": {
      "type": "object",
      "required": ["id", "title", "status", "explanation", "evidence", "fix_ids"],
      "properties": {
        "id":          { "$ref": "#/$defs/categoryId" },
        "title":       { "type": "string" },
        "status":      { "$ref": "#/$defs/status" },
        "explanation": { "type": "string", "minLength": 1, "maxLength": 200 },
        "evidence": {
          "type": "array", "maxItems": 8,
          "items": {
            "type": "object", "required": ["label", "value"],
            "properties": {
              "label":  { "type": "string" },
              "value":  { "type": "string" },
              "status": { "$ref": "#/$defs/status" }
            }
          }
        },
        "fix_ids": { "type": "array", "items": { "$ref": "#/$defs/fixId" } }
      }
    }
  }
}
```

Rules JSON Schema can't express (checked by `engine/tests/test_integrity.py`, §7.6): every `fix_ids` and `top_fixes` entry exists in `fixes[]`; `overall` equals the worst rated category; red/amber categories have ≥ 1 evidence row and ≥ 1 fix; `top_fixes` follows the §0.8 ranking.

The baseline file has its own schema, `baseline/software-baseline.schema.json` (fields in §2.8).

### Appendix B — Pinned dependency manifests

These are **all** the dependency manifests in the repo. The collector has no dependencies (PowerShell 5.1 in-box only, §1.10). `tools/issue-license.mjs` uses plain Node with no packages. Reasons per dependency: §1.10.

#### B.1 `desktop/package.json`

```json
{
  "name": "antigravity-desktop",
  "productName": "Antigravity",
  "version": "1.0.0",
  "private": true,
  "description": "Read-only cyber health check for small businesses",
  "author": "Team Antigravity",
  "main": "out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "typecheck": "tsc --noEmit -p tsconfig.node.json && tsc --noEmit -p tsconfig.web.json",
    "test": "vitest run",
    "dist:dir": "electron-vite build && electron-builder --win --dir",
    "dist": "electron-vite build && electron-builder --win nsis"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "3.0.1",
    "lucide-react": "0.471.0",
    "@radix-ui/react-slot": "1.1.1",
    "@radix-ui/react-progress": "1.1.1",
    "@radix-ui/react-separator": "1.1.1",
    "zod": "3.24.1"
  },
  "devDependencies": {
    "electron": "34.0.0",
    "electron-builder": "25.1.8",
    "electron-vite": "3.0.0",
    "vite": "6.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "typescript": "5.7.3",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "@types/node": "22.10.7",
    "tailwindcss": "4.0.0",
    "@tailwindcss/vite": "4.0.0",
    "tw-animate-css": "1.2.0",
    "vitest": "2.1.8",
    "@testing-library/react": "16.1.0",
    "jsdom": "25.0.1"
  }
}
```

`version` is `0.1.0` during Day 1 and bumped to `1.0.0` for RC1 (§8.7).

#### B.2 `landing/package.json`

```json
{
  "name": "antigravity-landing",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "3.0.1",
    "lucide-react": "0.471.0",
    "@radix-ui/react-slot": "1.1.1"
  },
  "devDependencies": {
    "vite": "6.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "typescript": "5.7.3",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "tailwindcss": "4.0.0",
    "@tailwindcss/vite": "4.0.0",
    "tw-animate-css": "1.2.0"
  }
}
```

#### B.3 `engine/requirements.txt` (runtime, bundled by PyInstaller)

```
pydantic==2.10.5
jsonschema==4.23.0
Jinja2==3.1.5
reportlab==4.2.5
packaging==24.2
```

#### B.4 `engine/requirements-dev.txt` (tests and build, not bundled)

```
pytest==8.3.4
pyinstaller==6.11.1
ruff==0.8.6
```

> Version note (repeated from §1.1): this is a known-compatible set; confirm the majors on prep night and **do not upgrade during the event**. The lockfiles (`package-lock.json`) pin transitive dependencies.

### Appendix C — Full annotated folder tree

Consolidates §1.7, §2.1, §3.1, §4.1, §5.1 and every addendum in §4–§8. Owner letters are final (**A** Tshedi, **B** Shakir, **C** Frank, **D** Schwan). *(ign)* = git-ignored. *(gen)* = generated by a build step.

```
antigravity/
├── README.md                                  [A] 10-line quickstart → docs/manual.md
├── .gitignore                                 [D] node_modules, .venv, dist, build, out, release, .offline,
│                                                  fallback/*, docs/security-evidence, tools/demo-tokens.txt,
│                                                  desktop/src/main/resource-hashes.json
├── .gitattributes                             [D] *.ps1 eol=crlf; *.json eol=lf
├── .editorconfig                              [D] utf-8-bom for *.ps1; 2-space JS; 4-space py/ps1
├── .github/
│   └── pull_request_template.md               [A] Appendix D checklist
├── .offline/                         (ign)        prep-night downloads (§1.5)
│   ├── wheelhouse/                                Python wheels
│   ├── docs/                                      saved reference pages
│   └── tools/                                     Procmon, Strings, Sigcheck, 7-Zip (§7.2)
│
├── shared/                                        THE CONTRACT (§0)
│   ├── contract/
│   │   ├── scan.schema.json                   [B] Appendix A.1
│   │   ├── report.schema.json                 [A] Appendix A.2
│   │   ├── types.ts                           [B] TS types generated from both schemas
│   │   └── CHANGELOG.md                       [B] versions + sign-off record (§8.4 15:30)
│   ├── fixtures/
│   │   ├── scan.healthy.json                  [B] §0.7 fixture 1
│   │   ├── scan.no-bitlocker.json             [B] §0.7 fixture 2
│   │   ├── scan.home-edition.json             [B] §0.7 variant
│   │   ├── scan.defender-off.json             [B] §0.7 fixture 3
│   │   ├── scan.xss.json                      [B] malicious app name for RPT-07 (§7.6)
│   │   ├── report.healthy.json        (gen)   [A] §2.11 step 5
│   │   ├── report.no-bitlocker.json   (gen)   [A]
│   │   ├── report.home-edition.json   (gen)   [A]
│   │   ├── report.defender-off.json   (gen)   [A]
│   │   └── report.xss.json            (gen)   [A]
│   └── license/
│       ├── public-key.pem                     [B] Ed25519 public key (§3.11)
│       └── demo-keys.md                       [B] 3 public demo tokens
│
├── collector/                                     BRICK B — PowerShell 5.1, read-only (§3)
│   ├── collector.ps1                          [B] entry: -OutputPath -DryRun -Only -MockFile -RunId; AG-PHASE markers
│   ├── lib/
│   │   ├── Common.ps1                         [B] Invoke-Probe, Read-Ag* readers, ConvertTo-IsoUtc, Write-ScanJson, hashing
│   │   └── Allowlist.ps1                      [B] permitted commands (§3.7)
│   ├── probes/
│   │   ├── Host.ps1                           [B]
│   │   ├── Backup.ps1                         [B]
│   │   ├── Patch.ps1                          [B]
│   │   ├── Software.ps1                       [B]
│   │   ├── Protection.ps1                     [B]
│   │   └── Recovery.ps1                       [B]
│   ├── mocks/                                     not shipped (§5.2)
│   │   ├── home-edition.ps1                   [B]
│   │   ├── defender-off.ps1                   [B]
│   │   ├── non-admin.ps1                      [B]
│   │   ├── stale-patches.ps1                  [B]
│   │   └── probe-throws.ps1                   [B]
│   └── tests/                                     not shipped
│       ├── Test-Collector.ps1                 [B] isolation test
│       ├── Test-ReadOnly.ps1                  [B] AST allow-list check
│       └── Test-Schema.ps1                    [B] validate via engine/tools/validate.py
│
├── engine/                                        BRICK A — Python 3.12 (§2)
│   ├── .venv/                         (ign)
│   ├── requirements.txt                       [A] Appendix B.3
│   ├── requirements-dev.txt                   [A] Appendix B.4
│   ├── engine.spec                            [A] PyInstaller one-folder (§2.12)
│   ├── antigravity_engine/
│   │   ├── __init__.py                        [A] __version__
│   │   ├── __main__.py                        [A] CLI --in --out --baseline --json-only --version
│   │   ├── contract.py                        [A] pydantic models
│   │   ├── parser.py                          [A] load + validate scan.json
│   │   ├── baseline.py                        [A] load + validate baseline
│   │   ├── clock.py                           [A] "now" = collected_at
│   │   ├── paths.py                           [A] resource() for frozen/dev
│   │   ├── scoring/
│   │   │   ├── __init__.py                    [A]
│   │   │   ├── result.py                      [A] CategoryResult, EvidenceRow
│   │   │   ├── backup.py                      [A] §2.5.1
│   │   │   ├── patch.py                       [A] §2.5.2
│   │   │   ├── software.py                    [A] §2.5.3
│   │   │   ├── protection.py                  [A] §2.5.4
│   │   │   ├── recovery.py                    [A] §2.5.5
│   │   │   └── fixes.py                       [A] catalogue (§2.9) + top-3 ranking
│   │   ├── aggregator.py                      [A] overall RAG
│   │   ├── risk.py                            [A] weighted score → summary
│   │   ├── report_model.py                    [A] build + validate report.json
│   │   ├── render/
│   │   │   ├── html.py                        [A] Jinja2, autoescape on
│   │   │   └── pdf.py                         [A code, C layout] ReportLab one-pager (§4.11)
│   │   └── templates/
│   │       └── report.html.j2                 [C design, A wiring] (§4.10)
│   ├── tools/
│   │   └── validate.py                        [A] schema gate: scan|report <file> (§6.3)
│   ├── tests/
│   │   ├── conftest.py                        [A] make_scan() helper
│   │   ├── test_backup.py                     [A]
│   │   ├── test_patch.py                      [A]
│   │   ├── test_software.py                   [A]
│   │   ├── test_protection.py                 [A]
│   │   ├── test_recovery.py                   [A]
│   │   ├── test_ranking.py                    [A]
│   │   ├── test_fixtures.py                   [A]
│   │   ├── test_cli.py                        [A]
│   │   ├── test_render.py                     [A] PDF one page, HTML escaping
│   │   └── test_integrity.py                  [A] RPT-01..03, 06 (§7.6)
│   ├── build/                         (ign)       PyInstaller work dir
│   └── dist/engine/                   (ign)       engine.exe + _internal/
│
├── baseline/
│   ├── software-baseline.json                 [A] curated versions, ASR list, OS support (§2.8)
│   ├── software-baseline.schema.json          [A]
│   └── README.md                              [A] how entries are chosen
│
├── desktop/                                       BRICKS C (renderer), B (license), D (main, build)
│   ├── package.json                           [C] Appendix B.1
│   ├── package-lock.json                      [C]
│   ├── .npmrc                                 [D] prefer-offline (§1.6)
│   ├── electron.vite.config.ts                [C]
│   ├── electron-builder.yml                   [D] §5.2
│   ├── tsconfig.json                          [C]
│   ├── tsconfig.node.json                     [C]
│   ├── tsconfig.web.json                      [C]
│   ├── components.json                        [C] shadcn
│   ├── vitest.config.ts                       [C]
│   ├── resources/icon.ico                     [C]
│   ├── release/                       (ign)       installers, win-unpacked, SHA256SUMS.txt
│   └── src/
│       ├── shared/ipc.ts                      [C+D] channels + types (§4.6)
│       ├── main/
│       │   ├── index.ts                       [D] lifecycle, security flags, spellcheck off
│       │   ├── ipc.ts                         [D] handlers
│       │   ├── paths.ts                       [D] dev vs packaged (§5.5)
│       │   ├── runs.ts                        [D] run folders, keep latest only
│       │   ├── integrity.ts                   [D] resource hash check (§7.8)
│       │   ├── resource-hashes.json   (gen)   [D] from installer/make-manifest.mjs
│       │   ├── mock.ts                        [C] AG_MOCK (dev only)
│       │   ├── license/
│       │   │   ├── verify.ts                  [B] Ed25519 verify (§3.11)
│       │   │   ├── verify.test.ts             [B]
│       │   │   └── store.ts                   [B] license.txt read/write
│       │   └── pipeline/
│       │       ├── runProcess.ts              [D] spawn, timeout, kill tree
│       │       ├── runCollector.ts            [D]
│       │       └── runEngine.ts               [D]
│       ├── preload/index.ts                   [D] contextBridge API
│       └── renderer/
│           ├── index.html                     [C] CSP
│           └── src/
│               ├── main.tsx                   [C]
│               ├── App.tsx                    [C] screen state machine
│               ├── env.d.ts                   [C]
│               ├── styles/globals.css         [C] Tailwind + RAG tokens
│               ├── lib/utils.ts               [C]
│               ├── lib/reportSchema.ts        [C] zod mirror of A.2
│               ├── lib/progress.ts            [C] progress model (§4.8)
│               ├── components/ui/             [C] shadcn generated
│               ├── components/
│               │   ├── StatusBadge.tsx        [C]
│               │   ├── CategoryCard.tsx       [C]
│               │   ├── EvidenceTable.tsx      [C]
│               │   ├── FixList.tsx            [C]
│               │   └── AdminHint.tsx          [C]
│               ├── screens/
│               │   ├── LicenseScreen.tsx      [C]
│               │   ├── ScanningScreen.tsx     [C]
│               │   ├── ResultsScreen.tsx      [C]
│               │   └── ErrorScreen.tsx        [C]
│               ├── mocks/report.all-states.json [C] §4.12
│               └── __tests__/
│                   ├── fixtures.test.tsx      [C]
│                   └── progress.test.ts       [C]
│
├── landing/                                       BRICK C — Vite + React on Vercel (§4.13)
│   ├── package.json                           [C] Appendix B.2
│   ├── package-lock.json                      [C]
│   ├── vite.config.ts                         [C]
│   ├── tsconfig.json                          [C]
│   ├── components.json                        [C]
│   ├── vercel.json                            [C]
│   ├── index.html                             [C]
│   ├── public/                                [C] screenshots, favicon
│   └── src/
│       ├── main.tsx                           [C]
│       ├── App.tsx                            [C]
│       ├── styles/globals.css                 [C]
│       └── components/ui/                     [C]
│
├── installer/                                     BRICK D (§5)
│   ├── build-all.ps1                          [D] contract-check → engine → manifest → collector tests → desktop → installer
│   ├── contract-check.ps1                     [B+D] schema gate end to end (§6.3)
│   ├── make-manifest.mjs                      [D] resource SHA-256 manifest (§7.8)
│   ├── checksums.ps1                          [D]
│   ├── smoke-test.ps1                         [D] -Phase AfterInstall|AfterUninstall
│   ├── installer.nsh                          [D] remove %LOCALAPPDATA%\Antigravity on uninstall
│   ├── expected-files.txt                     [D] INS-03 allow-list
│   └── stubs/
│       ├── collector-stub.ps1                 [D] isolation test (§5.10)
│       └── README.md                          [D]
│
├── tools/                                         dev-only, never packaged
│   ├── issue-license.mjs                      [B] keygen / sign (§3.11)
│   ├── demo-tokens.txt                (ign)   [B] incl. expired test token
│   └── security/
│       ├── Snapshot-State.ps1                 [B] §7.2
│       ├── Compare-State.ps1                  [B]
│       ├── Analyze-Procmon.ps1                [B]
│       └── ag-procmon.pmc                     [B] Procmon filter
│
├── fallback/                          (ign, except README) demo artefacts (§9.6)
│   └── README.md                              [C] what goes here and how it's made
│
└── docs/
    ├── manual.md                              [A] this manual, consolidated
    ├── decisions.md                           [A] one-line log: cuts, RCs, VM runs, ⚠ verify values
    ├── tickets.md                             [A] fallback ticket list (§8.9)
    ├── popia-note.md                          [B] what is and isn't collected
    ├── security-results.md                    [B] §7 pass/fail sheet (submitted)
    ├── security-evidence/             (ign)   [B] screenshots, logs
    ├── demo-script.md                         [C] §9.4 with real names/times
    ├── pitch-notes.md                         [C] notes from Day 2 talks
    ├── pitch-skeleton/                        [C] slide outline + screenshots
    └── demo/
        └── reset-demo.ps1                     [C] §9.6
```

### Appendix D — Git branch / PR checklist

Branches and rules: §1.9. Copy this into `.github/pull_request_template.md`.

**Before opening a PR (author)**

| # | Check |
|---|---|
| 1 | Branch name is `brick/<x>`, `contract/<topic>` or `fix/<short-name>` |
| 2 | `git pull --rebase origin main` done; no merge commits from `main` in your branch |
| 3 | Your brick's isolation test passes locally (§0.2) — paste the output in the PR |
| 4 | Commits follow `type(scope): message` (`feat(engine): …`, `fix(collector): …`, `contract: …`) |
| 5 | If you added a dependency: pinned version, lockfile committed, reason added to §1.10 / Appendix B |
| 6 | If you added a file: it's in the Appendix C tree (doc first — maintenance note) |
| 7 | No secrets, no real scan output, no personal data in the diff (`git diff --cached` checked) |
| 8 | After 06:00 Day 2: PR is labelled `security-critical` or `demo-blocking` (§8.6), otherwise don't open it |

**Reviewer**

| # | Check |
|---|---|
| 1 | Change matches the manual section it implements (or the manual was updated in the same PR) |
| 2 | Contract files untouched — or, if touched, all four members agreed in the team channel (maintenance note) |
| 3 | Collector PRs: `Test-ReadOnly.ps1` output says `READ-ONLY OK` |
| 4 | Pulled the branch and ran the isolation test yourself for non-trivial changes |

**Merging (Tshedi; Shakir if Tshedi unavailable > 30 min or asleep 02:00–04:00)**

| # | Check |
|---|---|
| 1 | Squash merge; message keeps the conventional prefix |
| 2 | Never force-push after 19:00 Day 1; revert instead |
| 3 | After merge: owners of affected bricks re-run their isolation tests; post "green" in chat |
| 4 | Milestone tags at the times in Appendix G: `pre-integration`, `merged-bricks`, `v0.1-integrated`, `v0.2-installer`, `v1.0.0-rc1`, `v1.0.0-rc2` (optional), `v1.0.0-demo` |

### Appendix E — Definition-of-done one-pagers

Consolidated from §0.3, §2.13, §3.13, §4.14, §5.10 and §7. "Due" refers to Appendix G.

#### E.1 Brick A — Assessment Engine (Tshedi)

| # | Criterion | How verified | Ref | Due |
|---|---|---|---|---|
| A1 | Parser validates input; bad input → exit 2 with all-`failed` report | `test_cli.py` | §2.4 | D1 18:00 |
| A2 | Every rule in §2.5 implemented with a test, boundaries included | `pytest -q` | §2.5, §2.10 | D1 00:00 |
| A3 | `unavailable` and `failed` handled separately; Home BitLocker rated amber | `test_protection.py`, `test_integrity.py` | §2.7 | D1 00:00 |
| A4 | Overall, risk summary, top-3 ranking correct | `test_ranking.py` | §2.6 | D1 21:00 |
| A5 | `report.json` validates against A.2 for all fixtures; UI fixtures regenerated | `test_fixtures.py`, `validate.py` | §2.11 | D1 21:00 |
| A6 | HTML self-contained and escaped; PDF exactly one page | `test_render.py`, RPT-07 | §4.10–4.11 | D1 00:00 |
| A7 | Baseline ≥ 10 entries with real versions and sources | Review | §2.8 | Pre-travel |
| A8 | No network imports | `Select-String` check | §2.13 | D1 00:00 |
| A9 | `engine.exe` runs on a machine without Python in < 5 s | Windows Sandbox / VM | §2.12 | D1 23:00 |

#### E.2 Brick B — Collector & License (Shakir)

| # | Criterion | How verified | Ref | Due |
|---|---|---|---|---|
| B1 | Static read-only check passes | `Test-ReadOnly.ps1` → `READ-ONLY OK` | §3.7 | D1 18:00 |
| B2 | Output validates against A.1, normal and elevated, on two machines | `validate.py scan` | §3.9 | D1 21:00 |
| B3 | All probes return `ok`/`unavailable`/`failed`; never throw to caller | `Test-Collector.ps1` with 5 mocks | §3.4, §3.10 | D1 00:00 |
| B4 | Full collection < 20 s on both machines | `duration_ms` | §3.9 | D1 21:00 |
| B5 | `-OutputPath`, `-DryRun`, `-Only`, `-MockFile`, `-RunId`, `AG-PHASE` markers | Manual run | §3.3, §4.8 | D1 21:15 |
| B6 | Every ⚠ verify value confirmed and logged | `docs/decisions.md` | §3.5 | Pre-travel |
| B7 | No usernames, paths, IPs or raw hostnames in output | PRV-04 | §7.5 | D1 02:00 |
| B8 | Licence: 3 demo + 1 expired token issued; private key off-repo and backed up | LIC-08, LIC-09 | §3.11 | Pre-travel |
| B9 | `verify.ts` rejects malformed, tampered, swapped, expired, unknown-key tokens; scan gated in main | `verify.test.ts`, LIC-01..07 | §3.11 | D1 21:00 |
| B10 | Read-only proven dynamically: snapshot diff, Procmon, audit log | RO-01..05 | §7.3 | D2 09:00 |

#### E.3 Brick C — Frontend & Reports (Frank)

| # | Criterion | How verified | Ref | Due |
|---|---|---|---|---|
| C1 | Four screens work in mock mode | `AG_MOCK=1` run | §4.9, §4.12 | D1 18:00 |
| C2 | All five statuses drawn with icon + text + colour | `fixtures.test.tsx` | §4.9.3 | D1 18:00 |
| C3 | Zod rejects malformed reports | Test | §4.9.3 | D1 21:00 |
| C4 | Progress model monotonic, never 100% early | `progress.test.ts` | §4.8 | D1 00:00 |
| C5 | Real scan in dev mode shows results < 60 s on Dev-1 and Dev-2 | Manual | §6.6 | D1 21:00 |
| C6 | PDF and HTML open from the app; same statuses everywhere | RPT-08 | §4.10–4.11 | D1 00:00 |
| C7 | HTML/PDF design and wording handed to Tshedi | Review | §4.11 | D1 21:30 |
| C8 | Landing page live on Vercel with working download link | Phone check | §4.13 | D2 11:30 |
| C9 | Fallback artefacts produced and copied to 3 locations | §9.6 table | §9.6 | D2 09:00 |
| C10 | Demo script rehearsed twice under time | Timer | §9.4 | D2 13:00 |

#### E.4 Brick D — Packaging & Deployment (Schwan)

| # | Criterion | How verified | Ref | Due |
|---|---|---|---|---|
| D1 | Main pipeline (paths, spawn, IPC) works with stubs | §5.10 isolation | §4.5–4.7, §5.5 | D1 18:00 |
| D2 | Kill-tree on cancel leaves no orphan processes | Task Manager | §4.7 | D1 21:00 |
| D3 | `build-all.ps1` green from a fresh clone, Wi-Fi off | Run | §5.8 | D1 00:00 |
| D4 | Packaged paths correct; no `tests/`/`mocks/` shipped | `dist:dir` inspection | §5.4–5.5 | D1 23:00 |
| D5 | Resource manifest blocks tampered resources | TMP-01..04 | §7.8 | D2 06:00 |
| D6 | Clean-VM test all 21 steps pass | §5.9 log | §5.9 | D2 09:00 |
| D7 | Install/uninstall leave no persistence or leftovers; no extra files | INS-03..05 | §7.9 | D2 09:00 |
| D8 | Installer < 200 MB; SHA-256 published | `checksums.ps1` | §5.8 | D2 11:25 |
| D9 | GitHub Release created; link handed to Frank | Release page | §5.8 | D2 11:25 |
| D10 | Demo laptop runs RC1, installed from USB | §9.7 | §5.7 | D2 09:00 |

### Appendix F — Glossary

| Term | Meaning in this project |
|---|---|
| **AG-PHASE** | Line the collector prints before each probe (`AG-PHASE:backup`) so the app can show progress (§4.8) |
| **AMSI** | Antimalware Scan Interface — lets Defender inspect PowerShell scripts as they run (§3.12) |
| **ASR** | Attack Surface Reduction rules — Defender rules that block common ransomware behaviours, e.g. Office spawning child processes (§2.5.4, §3.5) |
| **asar** | Electron's archive format holding the app's JavaScript (`app.asar`) |
| **Baseline** | Our curated JSON list of apps and their minimum safe versions (§2.8) |
| **BitLocker** | Windows full-disk encryption (Pro/Enterprise). Home has a limited "Device Encryption" instead |
| **Brick** | One team member's independently testable part of the product (§0.1) |
| **CFA** | Controlled Folder Access — Defender feature that stops unknown apps changing protected folders (§2.5.4) |
| **CLM** | Constrained Language Mode — locked-down PowerShell mode on some managed PCs (§3.6) |
| **Collector** | Brick B's read-only PowerShell script that produces `scan.json` |
| **Contract** | The two JSON schemas every brick codes against (§0, Appendix A) |
| **CSP** | Content Security Policy — browser rule limiting what the renderer can load or contact (§4.4) |
| **Ed25519** | Signature algorithm used for licence tokens (§3.11) |
| **Engine** | Brick A's Python program that scores `scan.json` and writes the reports |
| **Evidence row** | A label/value line in a category that shows *why* it got its status |
| **extraResources** | electron-builder setting that ships files outside the asar (§5.2) |
| **Fixture** | A saved example JSON file used for testing without the other bricks (§0.7) |
| **Hotfix / KB** | A Windows update, identified by a Knowledge Base number (`KB5044285`) |
| **IPC** | Inter-process communication between Electron's renderer and main process (§4.6) |
| **Isolation test** | A brick's own test that runs with no other brick present (§0.2) |
| **KFM** | OneDrive Known Folder Move — Desktop/Documents/Pictures synced to OneDrive |
| **Main / preload / renderer** | Electron's three layers: OS-level process, safe bridge, UI (§4.4) |
| **Mark of the Web (MOTW)** | Tag Windows adds to downloaded files; triggers SmartScreen (§5.7) |
| **MVP** | Minimum viable product: licence → scan < 60 s → 5-category HTML report → one-page PDF |
| **NSIS** | Nullsoft Scriptable Install System — the Windows installer format we build (§5.3) |
| **POPIA** | Protection of Personal Information Act (South Africa). We collect no personal information and keep everything on the PC (§7.5) |
| **Procmon** | Sysinternals Process Monitor — records every file, registry and network operation (§7.3) |
| **PyInstaller** | Turns the Python engine into `engine.exe` that runs without Python installed (§2.12) |
| **RAG** | Red / Amber / Green status rating |
| **RC** | Release candidate build (§8.7) |
| **Run folder** | `%LOCALAPPDATA%\Antigravity\runs\<run_id>\` holding one scan's files |
| **Shadow copy (VSS)** | Windows point-in-time snapshot; ransomware often deletes these, so they don't count as backups |
| **SmartScreen** | Windows warning shown for unsigned or uncommon downloads (§5.7) |
| **SMME** | Small, Medium and Micro Enterprise — South African term for small businesses |
| **Tamper Protection** | Defender setting that stops other software switching Defender off |
| **unavailable vs failed** | *unavailable* = we knew we couldn't check (no admin, Home edition); *failed* = we tried and it broke (§0.9) |
| **WinRE** | Windows Recovery Environment — used to repair or reset a PC that won't start |
| **Zod** | TypeScript library the UI uses to validate `report.json` (§4.9.3) |

### Appendix G — One-page timeline (print and tape to the table)

> Condensed from §8. Confirm programme times on arrival. **Lead / cut decisions: Tshedi.**

| Time | Programme | Antigravity does | Done means | If late → |
|---|---|---|---|---|
| **T−5 → T−1** | — | §1 setup, offline test, scaffold builds, VM, USB kit, baseline, keys | 4/4 green at T−1 20:00 call | Buddy session that night |
| **D1 <15:30** | Arrival | Laptops up, version checks. No code | — | Restore from USB |
| **15:30–16:00** | Challenge planning | Sign off §0 contract. **No code before sign-off** | 4 names in CHANGELOG | Sign §0 as written at 16:00 |
| **16:00–18:00** | Hacking | Brick skeletons + first isolation test | 4 bricks green, pushed | Rung 1: integrate with fixtures/stubs |
| **18:00–19:00** | Dinner | **No code.** Cross-review contract | Contract tickets | — |
| **19:00–21:00** | Hacking | §6 integration in dev mode. Force-push ban from 19:00 | Dev-mode scan → HTML · `v0.1-integrated` | Rung 2 (21:00): PDF → screenshot |
| **21:00–21:15** | Mentor check-in | 5-min dev-mode demo; log feedback as tickets | `mentor-d1-*` tickets | Show parts separately |
| **21:15–00:00** | Night shift | Schwan installer · Frank PDF · Tshedi scoring · Shakir read-only | Installer on clean-ish PC · `v0.2-installer` | Rung 4 (23:00): dev-mode + video |
| **00:00–02:00** | Overnight + mentors | §7 first pass: RO, LIC, PRV | Pass/fail sheet + tickets | Rung 5: critical fail → mentor; never ship silently |
| **02:00–04:00** | Shower slots | Awake: **Schwan + Shakir** (VM test, rendering, re-tests). Sleep: Frank + Tshedi | VM log line | Document failure for 04:00 |
| **04:00–06:00** | Shower slots | Awake: **Frank + Tshedi** (slides skeleton, rendering, fix list). Sleep: Schwan + Shakir | Slide skeleton; 06:00 fix list | Rung 6: portable zip fallback |
| **06:00–07:00** | — | **Feature freeze.** Fixes only. 06:45 build RC1 | `v1.0.0-rc1` | Last good overnight build |
| **07:00–08:00** | Breakfast | **Nobody codes** | — | — |
| **08:00–09:00** | Reset | RC1 clean-VM test · final §7 pass · fallback video/HTML/PDF/screens · demo laptop on RC1 | All artefacts in 3 places | Rung 8: submit last verified |
| **09:00–09:45** | SMME talk (on-topic) | **Frank + Tshedi attend** | Pitch notes | One of them at minimum |
| **09:45–10:00** | Talk | **Shakir attends** | — | — |
| **10:00–10:30** | Talk | **Schwan attends** | — | — |
| **10:30–11:00** | Final hacking | Critical fixes from test sheet only (≤ 15 min each). 10:55 RC2 if needed | RC1 final or RC2 building | Unmerged fixes dropped |
| **11:00–11:15** | Mentor checkpoint | 5-min installer demo on RC1 | Mentor notes | Fallback video |
| **11:15–11:45** | Submission prep | Choose RC · tag `v1.0.0-demo` · release · **SUBMIT BY 11:30** | Confirmation screenshot | Rung 10: submit what we have |
| **12:30–13:00** | Pitch prep | §9.7 checklist · rehearse twice | Two timed runs | Cut slides, not the scan |
| **13:00–14:10** | Pitches | §9.9 run sheet. Demo fallback closes at +8 min | — | F1–F4 (§9.5) |

### Appendix H — Change log (folded into this edition)

The section files were written one prompt at a time. Each later section recorded the changes it needed in earlier ones. **All of them are applied in this consolidated edition** — in the sections named and in the Appendix C tree. They are kept here so the team can see why the text differs from any earlier printout.

| Change | Where it now lives |
|---|---|
| Brick letters fixed: **A = Engine (Tshedi), B = Collector & License (Shakir)** | §0.1–§0.3, §1.5, §1.9, Appendix C |
| Collector flag `-Out` renamed `-OutputPath` | §1.4, §3.3 |
| Contract freeze moved to 16:00 Day 1; later changes need all four members | §0.10, §1.9, §8.4, Maintenance note |
| Collector `-RunId` parameter and `AG-PHASE:` progress markers | §3.2, §3.3, §4.7, §4.8 |
| `engine/tools/validate.py`, `engine/antigravity_engine/paths.py`, `test_render.py`, `test_integrity.py` | §2.1, §2.10, Appendix C |
| `installer/contract-check.ps1` and `installer/make-manifest.mjs` in `build-all.ps1` | §5.8 |
| Electron `spellcheck: false` | §4.4 |
| Security tools in the pre-travel download list; VM download starts at T−5 | §1.5, §8.3 |
| Integration windows 19:00–21:00 and 21:15–00:00; new milestone tags | §1.9, §6 intro, §8.4 |
| Release candidates RC1/RC2 replace a fresh 11:00 build | §5.8 steps 8–9, §8.7 |
| Schwan's 16:00–18:00 deliverable is the main-process pipeline with stubs | §5.10 |
| §7 first and final pass timings | §7.1 |
| New docs and demo files (`docs/pitch-notes.md`, `docs/tickets.md`, `docs/demo/reset-demo.ps1`, `fallback/`, `tools/security/*`, `installer/expected-files.txt`, `.github/pull_request_template.md`, `shared/fixtures/scan.xss.json`) | Appendix C |

The original change tables follow for reference. Where one disagrees with the body of the manual (for example the 21:15 additive-change window), the body is correct.

#### From §4–§5

These follow from §4–§5 and must be applied to §1–§3 in the consolidated manual. Contract-adjacent ones go through §0.10 before the 21:15 Day 1 freeze.

| # | Section | Change | Owner |
|---|---|---|---|
| 1 | §3.3 | Add parameter `-RunId <string>`: if given, used as `run_id` instead of generating one, so the run folder name (created by main, §5.6 step 8) matches `scan.json` (§0.5). Validate against `^[0-9TZ:-]+_[0-9a-f]{4}$` | B |
| 2 | §3.2 | Before each probe, when **not** `-DryRun`, write one line `AG-PHASE:<name>` to stdout via `Write-Output` (already allow-listed). Never in `-DryRun`, where stdout is the JSON | B |
| 3 | §1.7 | Add the ✚ files from §4.1 and §5.1 to the tree; add `desktop/release/` and `engine/build/` to `.gitignore` | D |
| 4 | §2.10 | Add `tests/test_render.py` (PDF single page, HTML autoescape) | A |
| 5 | §0.3 | Brick C "done" now also covers the HTML/PDF design hand-off (§4.10–4.11) | C |
| 6 | §1.4, §1.7 | `-Out` → `-OutputPath` (already noted after §3) | B |

#### From §6–§7

| # | Section | Change | Owner |
|---|---|---|---|
| 1 | §2.1, §1.7 | Add `engine/tools/validate.py`: `validate.py scan|report <file>` → validates against `/shared/contract/*.schema.json` with `jsonschema`, prints `VALID <kind> <version>` or `INVALID <json-path>: <message>`, exit 0/1 | A |
| 2 | §5.1, §5.8 | Add `installer/contract-check.ps1` (collector `-DryRun` → validate scan → engine `--json-only` → validate report → `CONTRACT OK`) and call it as step 0 of `build-all.ps1` | B, D |
| 3 | §5.1, §5.5, §5.8 | Add `installer/make-manifest.mjs` (run after PyInstaller, before `electron-vite build`) writing `desktop/src/main/resource-hashes.json`; add `desktop/src/main/integrity.ts` that verifies it before each scan in packaged mode (§7.8). Insert into `build-all.ps1` between steps 2 and 4 | D |
| 4 | §1.7 | Add `tools/security/` (`Snapshot-State.ps1`, `Compare-State.ps1`, `Analyze-Procmon.ps1`, `ag-procmon.pmc`) — test tools, never packaged | B |
| 5 | §4.4 | Add `spellcheck: false` to `webPreferences` (avoids any dictionary download) | D |
| 6 | §2.10 | Add `engine/tests/test_integrity.py` covering RPT-01, -02, -03, -06 | A |
| 7 | §5.1 | Add `installer/expected-files.txt` (generated once from a known-good `win-unpacked`, reviewed by hand) for INS-03 | D |
| 8 | §1.5 | Add Procmon, Strings, Sigcheck and 7-Zip to the download-before-travel checklist (`.offline/tools/`) | All |
| 9 | §1.9 | Add tag `merged-bricks` (§6.2 step 1.7) to the milestone tags | A |

#### From §8

| # | Section | Change |
|---|---|---|
| 1 | §1.9 timeline anchors | Contract **sign-off 16:00** (freeze for additive changes stays 21:15); `v0.1-integrated` moves from ~23:59 to **21:00**; add `v0.2-installer` (00:00), `v1.0.0-rc1` (06:45), `v1.0.0-rc2` (10:55, optional); `v1.0.0-demo` placed at **11:20**, not 11:00 |
| 2 | §5.8 step 8–9, §5.10 | Final build comes from RC1/RC2 per §8.7, not from a fresh tag at 11:00; GitHub Release by 11:25 |
| 3 | §6 intro | Integration window is 19:00–21:00 (Phases 1–3, 5) and 21:15–00:00 (Phases 4, 6) |
| 4 | §5.10 isolation | Schwan's 16:00–18:00 deliverable is the main-process pipeline with stubs (C3) |
| 5 | §1.5 | Add the T−3 / T−2 / T−1 deadlines and the T−1 20:00 go/no-go call from §8.3; Schwan starts the VM download at T−5 |
| 6 | §7.1 | First pass 00:00–02:00 (subset listed in §8.4); final pass 08:00–09:00 on RC1 |
| 7 | New files | `docs/pitch-notes.md`, `docs/pitch-skeleton/`, `docs/tickets.md` (fallback), `fallback/` (git-ignored except README) — add to §1.7 tree |

---

## Manual maintenance note

Keep this manual true for the whole event. Four rules:

1. **The data contract (§0, Appendix A) is frozen after 16:00 Day 1.** There is no "additive changes until 21:15" window (§0.10).
2. **Any contract change after 16:00 needs all four members to agree in the team channel.** Post the proposed change, wait for four explicit "agree" replies, then make one `contract/*` PR that updates §0, Appendix A, `CHANGELOG.md` and the fixtures together.
3. **The timeline (§8 and Appendix G) is re-baselined twice: 21:00 Day 1 and 08:00 Day 2.** Tshedi updates the remaining rows to reflect where the team really is, records any ladder rung taken in `docs/decisions.md`, re-prints Appendix G, and confirms roles for the rest rota (§8.5) and the pitch (§9.1).
4. **Doc first, then code.** Any gap found while building — a missing file, a wrong path, an unclear rule — is fixed in `docs/manual.md` first (in the same PR), then in the code. If the manual and the code disagree, the manual is wrong until it's updated, and the PR isn't merged until both match.

*End of the Team Antigravity Build & Integration Manual.*
