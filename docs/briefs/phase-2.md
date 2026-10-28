# Phase 2 brief: Read-only guard

Branch `brick/collector`. Manual §3.7. Not committed yet (waiting for `Verified`).

## 1. What was built

| File | What it does and why |
|---|---|
| `collector/tests/Test-ReadOnly.ps1` | The read-only guard. It reads every `.ps1` in `collector/` (except `tests\` and `mocks\`) with the PowerShell AST (abstract syntax tree: the parsed structure of the code, read without running it). It prints `READ-ONLY OK` (exit 0), or one line per problem as `relative\path.ps1:<line> <reason>` (exit 1). It does everything the §3.7 snippet does and more (see §6 D1). Optional `-Root` so it can be tested on sample folders. |
| `collector/tests/Test-ReadOnlyGuard.ps1` | 292 tests for the guard. Each one writes a small sample collector into a temp folder, runs the guard on it in a fresh `powershell.exe`, and checks the exit code and output. |
| `collector/lib/Common.ps1` | One line changed (line 37). `Invoke-Probe` now takes the error type name from `$_.CategoryInfo.Reason` instead of `$_.Exception.GetType().Name`. The text is the same, but there is no `GetType()` call, which the guard now bans. |
| `collector/docs/decisions.md` | First entries: the guard design and its known limits. |

`lib/Allowlist.ps1` is unchanged: exactly the 24 names from §3.7.

## 2. How it works

1. Loads the real `lib/Allowlist.ps1`. It never uses one found under `-Root`, so a sample folder can't bring its own allowlist.
2. Finds every `*.ps1` under the root, including hidden files. It skips a file only when the first folder of its **relative** path is `tests` or `mocks`. No files found → fail. That way an empty folder can't pass by default.
3. Parses each file. A parse error → fail, so a half-understood file can't pass.
4. Checks every part of the code against allowlists. Anything not listed fails:
   - **Commands:** the 24 allowlisted names, plus the collector's own functions. An own function must be defined exactly once, must not use a banned verb (§3.7 rule 1) and must not take over a real cmdlet's name. `Write-ScanJson` and `Invoke-Probe` may be defined only in `lib\Common.ps1`.
   - **Run-time calls** (`&` or `.` where the command is held in a variable or built while the script runs): allowed only at 6 pinned sites. Each pin is tied to its file, its function and what it means, not just its text. Examples: `& $Body` only inside `Invoke-Probe`, where `$Body` is a `[scriptblock]` parameter and is never assigned. `$probes` may appear only at its 3 exact spots in `collector.ps1`. reagentc only as the full-path call with exactly `/info`.
   - **.NET:** an allowlist of types, instance methods and `type::method` pairs. `[IO.File]` only as `::WriteAllText`, inside `Write-ScanJson`. `$var::X` is banned. Reflection properties (`Assembly`, `ImplementingType`, `PSObject` and the like) are banned. The one exception is `$p.PSObject.Properties`, as the loop collection in `Read-AgAsrRegistry`, which lists ASR rule GUIDs.
   - **Arguments:** `New-Object` only for `-ComObject Shell.Application` or `Text.UTF8Encoding`. `Get-CimInstance` only with a fixed class and namespace from a list. `ForEach-Object` only with a scriptblock. No `-ComputerName`, `-CimSession`, `-Session`, `-Query`, `-Credential` or `-*Variable` (including abbreviations). No splatting (passing parameters from a hashtable with `@name`).
   - **Paths:** the path arguments of `Get-ChildItem`, `Get-ItemProperty`, `Test-Path` and `Resolve-Path` must be fixed text, `$PSScriptRoot`/`$env:` strings, or variables set only from those. The `Variable:`, `Function:`, `Alias:`, `Env:`, `Cert:` and `WSMan:` drives and UNC paths (`\\server\...`) are banned.
   - **Writes:** no `>` file redirection (`2>&1` is fine). No assignment to `$env:`, to drive variables (`${C:\x}`), to scope-qualified variables (`$script:x`, `$global:x`), or to a property of a command's result.
   - **Other:** no `#requires`, no `using`.
   - **Banned words** anywhere in the text, comments included: `Win32_Product`, `vssadmin`, `wbadmin start`, `manage-bde`, `bcdedit`, `Checkpoint-Computer`, `reagentc /enable|/disable`, `-EncodedCommand`, `-WindowStyle Hidden`, `runas`.
5. Output shows relative paths only. A name containing `\`, `/` or `:` prints as `<redacted>`, so no user name or folder path reaches the output. If the guard itself breaks, it prints `guard internal error` and exits 1.

**What it touches:** the guard only reads `.ps1` files as text and parses them. It never runs them. The tests create temp folders under `%TEMP%` with `[IO.Directory]::CreateDirectory`, write sample files with `[IO.File]::WriteAllText`, and delete the folders in a `finally` block with `[IO.Directory]::Delete`. They use no `New-*` or `Remove-*` cmdlets. No registry, service, setting or network is touched.

## 3. Tests written

292 cases in `Test-ReadOnlyGuard.ps1`, grouped:

| Group | What it checks | Why it matters |
|---|---|---|
| Real collector passes | Exactly `READ-ONLY OK`, exit 0 | The guard mustn't block our own code |
| 17 banned verbs, `Invoke-WebRequest`/`RestMethod`/`Expression`, `Start-Process`, `Add-Type`, aliases (`iwr`, `rm`, `sc`, `iex`, `%`), unknown exes | Each is flagged with its line | §3.7 rules 1, 4 |
| Banned words in strings and comments | Each word, both places | §3.7 rules 3, 4, 6 |
| reagentc | `/info` passes; any other argument, a bare `reagentc.exe`, or a moved pin fails | Only `reagentc /info` may run |
| Run-time calls and pins | `& $x`, a built command name, `$probes` copied, piped or looped over, `$key` rewritten, a `$script:`/`$global:` write to a pinned variable, a second `Invoke-Probe`/`Write-ScanJson` | Stops a pinned call being made to run something else |
| .NET | `Assembly.GetType`, `ImplementingType`, `Process::Start`, `File::Delete`, `Directory::CreateDirectory`, `Net.WebClient`, `Win32.Registry`, `scriptblock::Create`, `SetEnvironmentVariable`, `GetTempFileName`, `$var::X`, the PSObject pin edges | Closes the reflection route to any type |
| Methods on objects | `.Stop()`, `.MoveTo()`, `ForEach-Object Delete`, Shell `Verbs().DoIt()`, `ServiceStop`, `ShellExecute` | No changing state through objects the collector is allowed to read |
| Cmdlet arguments | `-ComputerName`, `-Query`, split `Win32_Prod`+`uct`, splatting, `-OutVariable` | §3.7 rules 3, 7 |
| Paths and writes | `>` redirection, `${C:\x}`, `$env:` writes, `$ExecutionContext.InvokeProvider`, paths built at run time to `Variable:` and other drives, writes to command results | §3.7 rules 2, 5, 8 |
| Fail closed | Parse error, empty folder, a bad file under `tests\`/`mocks\` ignored, a checkout under a folder named `tests` still scanned, `#requires` | The guard can't pass by not looking |
| No leaks | Failure output has no absolute path and no user name | POPIA (South Africa's data-protection law), §3.4 rule 4 |
| Pending probes | Fails once any of the 6 placeholder probe names is really defined | Forces `$AgPendingProbes` to shrink in Phases 3–4 |
| Positive controls | Literal HKLM paths, `"$PSScriptRoot\probes\*.ps1"`, a foreach over a literal array, hashtable writes, the real pinned sites | The rules aren't so strict they block correct code |

## 4. Test results

Final gate (run from `C:\Users\HP\antigravity`):

```
Test-Common.ps1        22 passed, 0 failed
Test-Skeleton.ps1      14 passed, 0 failed
Test-ReadOnlyGuard.ps1 Passed: 292  Failed: 0
Test-ReadOnly.ps1      READ-ONLY OK      (exit 0)
```

Sample failure (one temp file containing `Set-ItemProperty`):

```
bad.ps1:1 command not allowed: Set-ItemProperty      (exit 1)
```

**Proof the tests came first.** Every round of tests was run before its fix, and the output was saved:

| Round | What it added | Failing run before the fix |
|---|---|---|
| 1 | The first 111 tests | `Passed: 0  Failed: 111`, e.g. `FAIL Verb Set- is flagged (Set-ItemProperty): Test-ReadOnly.ps1 does not exist` |
| 2 | Socrates's first bypasses | `Passed: 129  Failed: 90`, e.g. `FAIL b01 ForEach-Object -MemberName Delete flagged: exit code was 0` |
| 3 | PSObject pin | `Passed: 224  Failed: 2`, e.g. `FAIL Real collector passes ...: lib\Common.ps1:109 member not allowed: PSObject` |
| 4 | Scope prefixes | `Passed: 227  Failed: 16`, e.g. `FAIL Scope bypass: $global:probes written before & $probes[$key] flagged: exit code was 0: READ-ONLY OK` |
| 5 | `$probes` copied to another name | `Passed: 244  Failed: 12`, e.g. `FAIL Probes pin: a1 alias then element write flagged: exit code was 0: READ-ONLY OK` |
| 6 | Provider drives | `Passed: 264  Failed: 28` |

**Review (Socrates, 4 rounds).** Each round, Socrates wrote sample scripts (read by the guard, never run) that got `READ-ONLY OK` while doing something banned. The first round reached any .NET type through reflection, re-pointed pinned calls, overrode `$env:SystemRoot` to swap reagentc, and wrote files by redirection. The later rounds used `$global:probes`, a second name for `$probes`, and `Get-ChildItem ('Variable'+':\probes')`. Every finding got a failing test and a fix. You then asked to wrap up the phase, so the last fix (the provider-drive rule) has passed its tests but **was not re-examined by Socrates**.

## 5. Run it yourself

Working folder: `C:\Users\HP\antigravity`

```
powershell.exe -NoProfile -Command "& '.\collector\tests\Test-ReadOnly.ps1'; exit $LASTEXITCODE"
```
You should see `READ-ONLY OK`. Any other line names a file and line in `collector/` that breaks §3.7: fix the code, not the guard.

```
powershell.exe -NoProfile -Command "& '.\collector\tests\Test-ReadOnlyGuard.ps1'"
```
Takes a few minutes: every case starts a fresh PowerShell. The last line should be `Passed: 292  Failed: 0`. A `FAIL` line names the rule that has stopped working.

Phase 1 suites, in the same folder: `Test-Common.ps1` → `22 passed, 0 failed`; `Test-Skeleton.ps1` → `14 passed, 0 failed`.

Manual §6.3 and RO-04 run it as `powershell -NoProfile -ExecutionPolicy Bypass -File collector\tests\Test-ReadOnly.ps1`. That works the same way. In this session, Claude couldn't use `-ExecutionPolicy Bypass`.

## 6. Decisions and limits

- **D1. Differs from manual §3.7 (manual update needed).** The §3.7 snippet would fail on our own code: it doesn't allow `ConvertTo-IsoUtc`, `Write-ScanJson`, `ConvertTo-AgSafeError` or `Read-Ag*`. It also misses run-time calls, .NET calls and parse errors, and it skips any path containing `\tests\`. The guard is stricter and does everything the snippet does. The manual's §3.7 snippet should be replaced with a pointer to this file. Logged in `collector/docs/decisions.md`.
- **D2. More allowlists need Tshedi's review.** The allowed types, methods, static pairs, CIM classes, reflection denylist and pinned sites all sit in one block at the top of `Test-ReadOnly.ps1`. That block carries the same rule as `Allowlist.ps1`: adding to it needs Tshedi's review. Phase 3 will add a few entries (see the Phase 3 plan, D4).
- **D3. `$AgPendingProbes`.** It lets the 6 probe names (`Get-AgHost` … `Get-AgRecovery`) through until Phases 3–4 define them. A test fails as soon as any of them is defined, so the list must shrink.
- **D4. Changed Phase 1 code:** `Common.ps1:37`, as described in §1.
- **D5. `collector/docs/demo/reset-demo.ps1`** (empty) is scanned, as you decided. If it ever needs to change things on the PC, it must move out of `collector/`.
- **Limit L1. It is a filter, not a proof.** A static check for PowerShell can't be complete, because the language has too many indirect routes. Six rounds of attempted bypasses have been closed, but the guard doesn't prove the code safe on its own. Code review and the Phase 5 mock tests still matter.
- **Limit L2.** Reading a property on an allowed COM or CIM object is only checked against the reflection denylist. A property whose read had side effects would pass. Socrates found none among the objects we use.
- **Limit L3. `-MockFile` (§3.10)** dot-sources a file the guard never scans. The pins stop collector code from re-pointing it, but whoever passes `-MockFile` can run any script. **Open question for you:** keep it as the manual says, or restrict it to `collector\mocks\` (manual change, before Phase 5)?
- **Limit L4.** Only `*.ps1` is scanned. The loader only loads `probes\*.ps1`, and every other dot-source is pinned, so `.psm1`/`.psd1` files can't be loaded.
- The last fix (provider drives) wasn't re-reviewed by Socrates, at your request (§4).

## 7. Pitch line

"Every build is checked by a guard that reads every line of the scanner and refuses anything not on an allowlist, so the scanner cannot change, delete or send anything on a customer's PC."
