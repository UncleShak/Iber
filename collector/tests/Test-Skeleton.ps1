# Phase 1 tests for collector.ps1 skeleton (manual 3.2, 3.3), run in child processes
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$collector = Join-Path $root 'collector.ps1'
$stub = Join-Path $PSScriptRoot 'stubs\stub-probes.ps1'

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
function Invoke-Collector([string[]]$CollectorArgs, [string]$Mock = $stub) {
    Invoke-Native (@('-NoProfile', '-File', $collector) + $CollectorArgs + @('-MockFile', $Mock))
}
function Assert-CleanErr([string]$Err, [string]$Fixed) {
    Assert-True ($Err -eq $Fixed) "stderr was '$Err'"
    Assert-True (-not $Err.Contains($root)) 'stderr contains repo path'
    Assert-True ($Err -notmatch ('(?<![A-Za-z0-9])' + [regex]::Escape($env:USERNAME) + '(?![A-Za-z0-9])')) 'stderr contains user name'
}
function Assert-Run($r) {
    if (-not [IO.File]::Exists($collector)) { throw 'collector.ps1 does not exist' }
}

Test-Case 'No OutputPath and no DryRun exits 64' {
    Assert-Run
    $r = Invoke-Collector @()
    Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
    Assert-CleanErr $r.Err 'Use -OutputPath <file> or -DryRun'
}
Test-Case 'Bad RunId fails and writes nothing' {
    Assert-Run
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Invoke-Collector @('-OutputPath', $p, '-RunId', 'bad')
        Assert-True ($r.Code -ne 0) 'exit code was 0'
        Assert-True (-not [IO.File]::Exists($p)) 'file was written'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Bad -Only value fails' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun', '-Only', 'Nope')
    Assert-True ($r.Code -ne 0) 'exit code was 0'
}
Test-Case 'DryRun emits valid contract header' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun')
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    Assert-True (-not ($r.Lines | Where-Object { $_ -like 'AG-PHASE*' })) 'AG-PHASE marker in DryRun'
    $o = $r.Text | ConvertFrom-Json
    $names = @($o.PSObject.Properties.Name) -join ','
    $exp = 'schema_version,run_id,collected_at,collector_version,duration_ms,host,backup,patch,software,protection,recovery'
    Assert-True ($names -eq $exp) "key order was $names"
    Assert-True ($o.schema_version -eq '1.0.0') 'schema_version'
    Assert-True ($o.collector_version -eq '0.1.0') 'collector_version'
    Assert-True ($o.run_id -match '^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[0-9a-f]{4}$') "run_id was $($o.run_id)"
    Assert-True ($o.collected_at -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$') "collected_at was $($o.collected_at)"
    Assert-True (($o.duration_ms -is [int] -or $o.duration_ms -is [long]) -and $o.duration_ms -ge 0) 'duration_ms'
}
Test-Case 'DryRun honours supplied RunId' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun', '-RunId', '2026-11-14T16-42-07Z_7f3a')
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    Assert-True ((($r.Text | ConvertFrom-Json).run_id) -eq '2026-11-14T16-42-07Z_7f3a') 'run_id differs'
}
Test-Case 'OutputPath writes file and phase markers' {
    Assert-Run
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Invoke-Collector @('-OutputPath', $p)
        Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
        Assert-True ([IO.File]::Exists($p)) 'file missing'
        $b = [IO.File]::ReadAllBytes($p)
        Assert-True (-not ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)) 'BOM present'
        $o = [IO.File]::ReadAllText($p) | ConvertFrom-Json
        Assert-True ($null -ne $o.schema_version) 'does not parse as scan'
        $exp = (@('host','backup','patch','software','protection','recovery') | ForEach-Object { "AG-PHASE:$_" }) -join ','
        $got = ($r.Lines | Where-Object { $_.Trim() -ne '' } | ForEach-Object { $_.Trim() }) -join ','
        Assert-True ($got -eq $exp) "stdout was $got"
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'DryRun with OutputPath creates no file' {
    Assert-Run
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Invoke-Collector @('-DryRun', '-OutputPath', $p)
        Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
        Assert-True (-not [IO.File]::Exists($p)) 'file was created'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Only Host,Patch limits sections' {
    Assert-Run
    $cmd = "& '$collector' -DryRun -Only Host,Patch -MockFile '$stub'"
    $prevEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = & powershell.exe -NoProfile -Command $cmd 2>$null; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevEap }
    $r = [pscustomobject]@{ Code = $code; Text = (@($out) -join "`n") }
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    $o = $r.Text | ConvertFrom-Json
    $names = @($o.PSObject.Properties.Name)
    Assert-True ($names -contains 'host' -and $names -contains 'patch') 'host/patch missing'
    foreach ($n in 'backup','software','protection','recovery') {
        Assert-True ($names -notcontains $n) "$n present"
    }
}
Test-Case 'Only Protection via -File limits sections' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun', '-Only', 'Protection')
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    $names = @(($r.Text | ConvertFrom-Json).PSObject.Properties.Name)
    Assert-True ($names -contains 'protection') 'protection missing'
    foreach ($n in 'host','backup','patch','software','recovery') {
        Assert-True ($names -notcontains $n) "$n present"
    }
}
Test-Case 'Unwritable OutputPath exits 70 and creates no folder' {
    Assert-Run
    $dir = New-TempDir
    try {
        $p = Join-Path (Join-Path $dir 'missing') 'scan.json'
        $r = Invoke-Collector @('-OutputPath', $p)
        Assert-True ($r.Code -eq 70) "exit code was $($r.Code)"
        Assert-CleanErr $r.Err 'Cannot write output'
        Assert-True (-not [IO.Directory]::Exists((Join-Path $dir 'missing'))) 'folder was created'
    } finally { [IO.Directory]::Delete($dir, $true) }
}

Test-Case 'Missing MockFile exits 64 with fixed text' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun') ($root + '\nope-mock.ps1')
    Assert-True ($r.Code -eq 64) "exit code was $($r.Code)"
    Assert-CleanErr $r.Err 'Mock file not found'
}
Test-Case 'Uncaught probe error exits 1 with fixed text' {
    Assert-Run
    $dir = New-TempDir
    try {
        $m = Join-Path $dir 'mock-throw.ps1'
        $body = ". '$stub'`r`nfunction Get-AgHost { throw 'boom' }`r`n"
        [IO.File]::WriteAllText($m, $body, (New-Object Text.UTF8Encoding $false))
        $r = Invoke-Collector @('-DryRun') $m
        Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
        Assert-CleanErr $r.Err 'Collector failed'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Mock override of Read-AgEdition reaches output' {
    Assert-Run
    $r = Invoke-Collector @('-DryRun') (Join-Path $PSScriptRoot 'stubs\mock-edition.ps1')
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    Assert-True ((($r.Text | ConvertFrom-Json).host.os_edition) -eq 'MockCore') 'os_edition not MockCore'
}
Test-Case 'Run under th-TH culture keeps Gregorian year' {
    Assert-Run
    $cmd = "[Threading.Thread]::CurrentThread.CurrentCulture='th-TH'; & '$collector' -DryRun -MockFile '$stub'"
    $r = Invoke-Native @('-NoProfile', '-Command', $cmd)
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code)"
    $o = $r.Text | ConvertFrom-Json
    Assert-True ($o.run_id.StartsWith('20')) "run_id was $($o.run_id)"
    Assert-True ($o.collected_at.StartsWith('20')) "collected_at was $($o.collected_at)"
}
Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
