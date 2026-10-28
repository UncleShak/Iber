# Phase 7 tests: -RunId, AG-PHASE markers, exit 64 on bad arguments (manual 3.3, 4.8)
# and installer/contract-check.ps1 (5.8, 6.3 step 2.8). Run in child processes.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$repo = Split-Path -Parent $root
$collector = Join-Path $root 'collector.ps1'
$stub = Join-Path $PSScriptRoot 'stubs\stub-probes.ps1'
$check = Join-Path $repo 'installer\contract-check.ps1'
$fixtures = Join-Path $repo 'shared\fixtures'

$script:passed = 0
$script:failed = 0
function Test-Case([string]$Name, [scriptblock]$Body) {
    try {
        & $Body | Out-Null
        Write-Output "PASS $Name"
        $script:passed++
    } catch {
        $m = ($_.Exception.Message -split "`r?`n")[0]
        Write-Output "FAIL ${Name}: $m"
        $script:failed++
    }
}
function Assert-True($Cond, [string]$Msg) { if (-not $Cond) { throw $Msg } }

function New-TempDir {
    $d = Join-Path ([IO.Path]::GetTempPath()) ('ag-test-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($d)
    return $d
}
function Invoke-Native([string[]]$ArgList) {
    $prevEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $all = & powershell.exe @ArgList 2>&1; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevEap }
    $outL = @($all | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { [string]$_ })
    $errL = @($all | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { ([string]$_).Trim() })
    [pscustomobject]@{ Code = $code; Lines = $outL; Text = ($outL -join "`n"); Err = ($errL -join "`n") }
}
function Invoke-Collector([string[]]$CollectorArgs) {
    Invoke-Native (@('-NoProfile', '-File', $collector) + $CollectorArgs + @('-MockFile', $stub))
}
function Invoke-Check([string[]]$CheckArgs = @()) {
    if (-not [IO.File]::Exists($check) -or (Get-Item -LiteralPath $check).Length -eq 0) { throw 'contract-check.ps1 is empty or missing' }
    Invoke-Native (@('-NoProfile', '-File', $check) + $CheckArgs)
}
function Assert-CleanErr([string]$Err, [string]$Fixed) {
    Assert-True ($Err -eq $Fixed) "stderr was '$Err'"
    Assert-True (-not $Err.Contains($repo)) 'stderr contains repo path'
}
function Get-LastLine($r) { @($r.Lines | Where-Object { $_.Trim() -ne '' })[-1].Trim() }

# ---- Collector: -RunId and exit codes (3.3) ----
Test-Case 'Bad RunId exits 64 with fixed text and writes nothing' {
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Invoke-Collector @('-OutputPath', $p, '-RunId', 'bad')
        Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
        Assert-CleanErr $r.Err 'Bad -RunId'
        Assert-True (-not [IO.File]::Exists($p)) 'file was written'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Upper-case hex RunId exits 64 (schema wants lower case)' {
    $r = Invoke-Collector @('-DryRun', '-RunId', '2026-11-14T21-30-00Z_ABCD')
    Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
}
Test-Case 'RunId with trailing newline exits 64' {
    $r = Invoke-Collector @('-DryRun', '-RunId', "2026-11-14T21-30-00Z_abcd`n")
    Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
}
Test-Case 'Bad -Only value exits 64 with fixed text' {
    $r = Invoke-Collector @('-DryRun', '-Only', 'Nope')
    Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
    Assert-CleanErr $r.Err 'Bad -Only value'
}
Test-Case 'OutputPath with RunId writes that run_id' {
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $id = '2026-11-14T21-30-00Z_0001'
        $r = Invoke-Collector @('-OutputPath', $p, '-RunId', $id)
        Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
        $o = [IO.File]::ReadAllText($p) | ConvertFrom-Json
        Assert-True ($o.run_id -eq $id) "run_id was $($o.run_id)"
    } finally { [IO.Directory]::Delete($dir, $true) }
}

# ---- Collector: AG-PHASE markers (4.8) ----
Test-Case 'Only Backup with OutputPath prints exactly AG-PHASE:backup' {
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Invoke-Collector @('-OutputPath', $p, '-Only', 'Backup')
        Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
        $got = ($r.Lines | Where-Object { $_.Trim() -ne '' } | ForEach-Object { $_.Trim() }) -join ','
        Assert-True ($got -eq 'AG-PHASE:backup') "stdout was $got"
    } finally { [IO.Directory]::Delete($dir, $true) }
}

# ---- installer/contract-check.ps1 (5.8, 6.3) ----
Test-Case 'contract-check passes on this PC and prints CONTRACT OK' {
    $r = Invoke-Check
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code): $($r.Text) $($r.Err)"
    Assert-True ((Get-LastLine $r) -eq 'CONTRACT OK') "last line was '$(Get-LastLine $r)'"
}
Test-Case 'contract-check passes every scan fixture' {
    $files = [IO.Directory]::GetFiles($fixtures, 'scan.*.json')
    Assert-True ($files.Count -ge 5) "only $($files.Count) scan fixtures found"
    foreach ($f in $files) {
        $r = Invoke-Check @('-ScanFile', $f)
        $n = [IO.Path]::GetFileName($f)
        Assert-True ($r.Code -eq 0) "$n exit code was $($r.Code): $($r.Text)"
        Assert-True ((Get-LastLine $r) -eq 'CONTRACT OK') "$n last line was '$(Get-LastLine $r)'"
    }
}
Test-Case 'contract-check fails loudly on a broken scan' {
    $dir = New-TempDir
    try {
        $o = [IO.File]::ReadAllText((Join-Path $fixtures 'scan.healthy.json')) | ConvertFrom-Json
        $o.run_id = 'bad'
        $p = Join-Path $dir 'scan.json'
        [IO.File]::WriteAllText($p, (ConvertTo-Json -InputObject $o -Depth 8), (New-Object Text.UTF8Encoding $false))
        $r = Invoke-Check @('-ScanFile', $p)
        Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
        Assert-True ($r.Lines -match '^INVALID \$\.run_id') "no INVALID run_id line: $($r.Text)"
        Assert-True ((Get-LastLine $r) -eq 'CONTRACT BROKEN at scan') "last line was '$(Get-LastLine $r)'"
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'contract-check fails when the engine exits 2' {
    $dir = New-TempDir
    try {
        # Stub Python: the engine (-m) exits 2 like invalid input (2.4); validate.py runs for real.
        $real = Join-Path $repo 'engine\.venv\Scripts\python.exe'
        $py = Join-Path $dir 'python.cmd'
        [IO.File]::WriteAllText($py, "@echo off`r`nif ""%1""==""-m"" exit /b 2`r`n""$real"" %*`r`n", (New-Object Text.ASCIIEncoding))
        $r = Invoke-Check @('-ScanFile', (Join-Path $fixtures 'scan.healthy.json'), '-Python', $py)
        Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
        Assert-True ($r.Lines -contains 'VALID scan 1.0.0') "scan step did not run: $($r.Text)"
        Assert-True ((Get-LastLine $r) -eq 'CONTRACT BROKEN at engine') "last line was '$(Get-LastLine $r)'"
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'contract-check fails when engine Python is missing' {
    $r = Invoke-Check @('-Python', (Join-Path $repo 'nope\python.exe'))
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    Assert-True ((Get-LastLine $r) -eq 'CONTRACT BROKEN at setup') "last line was '$(Get-LastLine $r)'"
}

Write-Output ''
Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 }
exit 0
