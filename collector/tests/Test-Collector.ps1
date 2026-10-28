# Phase 5 tests: collector.ps1 run per mock file (manual 3.10), child processes. Host and Protection only for now;
# Phase 4 turns the two PENDING cases on. Case mocks dot-source mocks\healthy.ps1 first, so mock runs never read this PC.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$collector = Join-Path $root 'collector.ps1'
$mocks = Join-Path $root 'mocks'
$repo = Split-Path -Parent $root
$venvPy = Join-Path $repo 'engine\.venv\Scripts\python.exe'
$schema = Join-Path $repo 'shared\contract\scan.schema.json'

$script:passed = 0
$script:failed = 0
$script:pending = 0
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
function Test-Pending([string]$Name, [string]$Why) { Write-Output "PEND ${Name}: $Why"; $script:pending++ }
function Assert-True($Cond, [string]$Msg) { if (-not $Cond) { throw $Msg } }

function Invoke-Run([string]$MockName) {
    $cmd = "& '$collector' -DryRun -Only Host,Protection"
    if ($MockName) {
        $m = Join-Path $mocks ($MockName + '.ps1')
        if (-not [IO.File]::Exists($m)) { throw "mock $MockName.ps1 does not exist" }
        $cmd += " -MockFile '$m'"
    }
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $all = & powershell.exe -NoProfile -Command ($cmd + '; exit $LASTEXITCODE') 2>&1; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prev }
    $text = (@($all | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { [string]$_ })) -join "`n"
    Assert-True ($code -eq 0) "collector exit code was $code"
    $scan = $text | ConvertFrom-Json
    Assert-True ($null -ne $scan.host -and $null -ne $scan.protection) 'host or protection missing'
    return [pscustomobject]@{ Scan = $scan; Text = $text }
}
function Assert-SchemaValid([string]$Json) {
    if (-not [IO.File]::Exists($venvPy)) { throw 'engine venv not found' }
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('ag-scan-' + [Guid]::NewGuid().ToString('N') + '.json')
    [IO.File]::WriteAllText($tmp, $Json, (New-Object Text.UTF8Encoding $false))
    $py = @'
import json, sys
from jsonschema import Draft202012Validator
s = json.load(open(sys.argv[1], encoding="utf-8"))
d = json.load(open(sys.argv[2], encoding="utf-8-sig"))
bad = 0
for k in ("host", "protection"):
    sub = dict(s["properties"][k]); sub["$defs"] = s["$defs"]
    for e in Draft202012Validator(sub).iter_errors(d[k]):
        print(k + ": " + e.message[:80]); bad += 1
sys.exit(1 if bad else 0)
'@
    try {
        $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $out = $py | & $venvPy -I - $schema $tmp 2>&1
        $code = $LASTEXITCODE
        $ErrorActionPreference = $prev
    } finally { [IO.File]::Delete($tmp) }
    Assert-True ($code -eq 0) ('schema invalid: ' + (($out | Select-Object -First 2) -join ' | '))
}
function Assert-ProtectionShape($Scan) {
    $keys = @($Scan.protection.PSObject.Properties.Name) -join ','
    Assert-True ($keys -eq 'bitlocker,defender,cfa,asr') "protection keys were $keys"
    foreach ($k in @('bitlocker', 'defender', 'cfa', 'asr')) {
        Assert-True (@('ok', 'unavailable', 'failed') -contains $Scan.protection.$k.status) "$k has no valid status"
    }
}

Test-Case 'healthy: sections present, all ok, schema-valid' {
    $r = Invoke-Run 'healthy'
    Assert-ProtectionShape $r.Scan
    foreach ($k in @('bitlocker', 'defender', 'cfa', 'asr')) { Assert-True ($r.Scan.protection.$k.status -eq 'ok') "$k status $($r.Scan.protection.$k.status)" }
    Assert-SchemaValid $r.Text
}
Test-Case 'home-edition: bitlocker unavailable, error mentions Home' {
    $b = (Invoke-Run 'home-edition').Scan.protection.bitlocker
    Assert-True ($b.status -eq 'unavailable') "status was $($b.status)"
    Assert-True ($b.error -like '*Home*') 'error does not mention Home'
}
Test-Case 'defender-off: defender ok, antivirus_enabled false' {
    $d = (Invoke-Run 'defender-off').Scan.protection.defender
    Assert-True ($d.status -eq 'ok') "status was $($d.status)"
    Assert-True ($d.antivirus_enabled -eq $false) 'antivirus_enabled not false'
}
Test-Case 'non-admin: not admin, nothing failed, bitlocker ok or needs admin' {
    $s = (Invoke-Run 'non-admin').Scan
    Assert-True ($s.host.is_admin -eq $false) 'is_admin not false'
    foreach ($k in @('bitlocker', 'defender', 'cfa', 'asr')) { Assert-True ($s.protection.$k.status -ne 'failed') "$k failed" }
    $b = $s.protection.bitlocker
    Assert-True ($b.status -eq 'ok' -or ($b.status -eq 'unavailable' -and $b.error -eq 'Requires administrator rights')) "bitlocker was $($b.status)"
}
# reads this PC, read-only: -DryRun, no mock. Asserts shape and statuses only; real values are never printed.
Test-Case 'no mock: shape and statuses (reads this PC, read-only)' {
    $r = Invoke-Run $null
    Assert-ProtectionShape $r.Scan
    Assert-True ($r.Scan.host.is_admin -is [bool]) 'is_admin not bool'
    Assert-True ($r.Scan.host.hostname_hash -match '^sha256:[0-9a-f]{64}$') 'hostname_hash shape'
    Assert-SchemaValid $r.Text
}
Test-Pending 'stale-patches' 'needs Phase 4 probes'
Test-Pending 'probe-throws' 'needs Phase 4 probes'

Write-Output "$script:passed passed, $script:failed failed, $script:pending pending"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
