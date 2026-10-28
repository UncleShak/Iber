# installer/contract-check.ps1 - schema gate end to end (manual 5.8, 6.3 step 2.8). Windows PowerShell 5.1.
# collector -DryRun -> validate.py scan -> engine --json-only -> validate.py report -> "CONTRACT OK" (exit 0).
# Any failure prints "CONTRACT BROKEN at <step>" and exits 1, so no installer is built across a broken contract.
# Reads this PC only through the read-only collector; writes only under out\contract-check\ (git-ignored).
[CmdletBinding()]
param(
    [string] $ScanFile,   # check this scan.json instead of running the collector (fixtures, tests)
    [string] $Python      # engine Python; default engine\.venv\Scripts\python.exe (override for tests)
)
$ErrorActionPreference = 'Stop'
$repo      = Split-Path -Parent $PSScriptRoot
$engineDir = Join-Path $repo 'engine'
$validate  = Join-Path $engineDir 'tools\validate.py'
$baseline  = Join-Path $repo 'baseline\software-baseline.json'
$collector = Join-Path $repo 'collector\collector.ps1'
$work      = Join-Path $repo 'out\contract-check'
if (-not $Python) { $Python = Join-Path $engineDir '.venv\Scripts\python.exe' }

function Exit-Broken([string]$Step, [string]$Why) {
    if ($Why) { Write-Output $Why }
    Write-Output "CONTRACT BROKEN at $Step"
    exit 1
}
# Runs a program and echoes its output (stdout unless -Quiet, and stderr). Results go to
# $script:StepCode / $script:StepLines, not the pipeline, so the echo is never captured by an assignment.
function Invoke-Step([string]$Exe, [string[]]$ArgList, [switch]$Quiet) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $all = & $Exe @ArgList 2>&1; $script:StepCode = $LASTEXITCODE } finally { $ErrorActionPreference = $prev }
    $script:StepLines = @($all | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { [string]$_ })
    if (-not $Quiet) { $script:StepLines }
    $all | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { ([string]$_).TrimEnd() }
}

# ---- 0. Setup ----
if (-not [IO.File]::Exists($Python))   { Exit-Broken 'setup' 'Engine Python not found (create engine\.venv, manual 2.2)' }
if (-not [IO.File]::Exists($validate)) { Exit-Broken 'setup' 'engine\tools\validate.py not found' }
if (-not [IO.File]::Exists($baseline)) { Exit-Broken 'setup' 'baseline\software-baseline.json not found' }
[void][IO.Directory]::CreateDirectory($work)
foreach ($f in 'report.json', 'evidence.json') { [IO.File]::Delete((Join-Path $work $f)) }   # no stale pass

# ---- 1. Collector -DryRun (or a given file) ----
$scanPath = Join-Path $work 'scan.json'
if ($ScanFile) {
    $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ScanFile)
    if (-not [IO.File]::Exists($full)) { Exit-Broken 'setup' 'Scan file not found' }
    Write-Output '1/4 Scan file given, collector skipped'
    $scanPath = $full
} else {
    Write-Output '1/4 Collector -DryRun'
    [IO.File]::Delete($scanPath)
    Invoke-Step 'powershell.exe' @('-NoProfile', '-File', $collector, '-DryRun') -Quiet
    if ($StepCode -ne 0) { Exit-Broken 'collector' "Collector exit code $StepCode" }
    [IO.File]::WriteAllText($scanPath, ($StepLines -join "`n"), (New-Object Text.UTF8Encoding $false))
}

# ---- 2. Schema gate on scan.json ----
Write-Output '2/4 validate.py scan'
Invoke-Step $Python @($validate, 'scan', $scanPath)
if ($StepCode -ne 0) { Exit-Broken 'scan' }

# ---- 3. Engine, JSON only (cwd must be the engine folder, manual 4.7) ----
Write-Output '3/4 engine --json-only'
Push-Location -LiteralPath $engineDir
try {
    Invoke-Step $Python @('-m', 'antigravity_engine', '--in', $scanPath, '--out', $work, '--baseline', $baseline, '--json-only')
} finally { Pop-Location }
if ($StepCode -ne 0) { Exit-Broken 'engine' "Engine exit code $StepCode" }

# ---- 4. Schema gate on report.json ----
Write-Output '4/4 validate.py report'
Invoke-Step $Python @($validate, 'report', (Join-Path $work 'report.json'))
if ($StepCode -ne 0) { Exit-Broken 'report' }

Write-Output 'CONTRACT OK'
exit 0
