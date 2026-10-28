# Phase 5 tests: collector.ps1 run per mock file (manual 3.10), child processes.
# Case mocks dot-source mocks\healthy.ps1 first, so mock runs never read this PC.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$collector = Join-Path $root 'collector.ps1'
$mocks = Join-Path $root 'mocks'
$repo = Split-Path -Parent $root
$venvPy = Join-Path $repo 'engine\.venv\Scripts\python.exe'
$schema = Join-Path $repo 'shared\contract\scan.schema.json'

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

function Invoke-Run([string]$MockName) {
    $cmd = "& '$collector' -DryRun"
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
for e in Draft202012Validator(s).iter_errors(d):
    print("/".join(str(p) for p in e.absolute_path) + ": " + e.message[:80]); bad += 1
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

$sections = @('host', 'backup', 'patch', 'software', 'protection', 'recovery')
function Get-AllStatuses($Scan) {
    $out = [ordered]@{}
    foreach ($k in @('backup', 'patch', 'software', 'recovery')) { $out[$k] = $Scan.$k.status }
    foreach ($k in @('bitlocker', 'defender', 'cfa', 'asr')) { $out["protection.$k"] = $Scan.protection.$k.status }
    return $out
}
function Assert-AllSections($Scan) {
    foreach ($k in $sections) { Assert-True ($null -ne $Scan.$k) "section $k missing" }
    Assert-ProtectionShape $Scan
    foreach ($k in @('backup', 'patch', 'software', 'recovery')) {
        Assert-True (@('ok', 'unavailable', 'failed') -contains $Scan.$k.status) "$k has no valid status"
    }
}

Test-Case 'healthy: all sections present, all ok, whole document schema-valid' {
    $r = Invoke-Run 'healthy'
    Assert-AllSections $r.Scan
    $st = Get-AllStatuses $r.Scan
    foreach ($k in $st.Keys) { Assert-True ($st[$k] -eq 'ok') "$k status $($st[$k])" }
    Assert-SchemaValid $r.Text
}
Test-Case 'home-edition: bitlocker unavailable, error mentions Home' {
    $r = Invoke-Run 'home-edition'; Assert-SchemaValid $r.Text; $b = $r.Scan.protection.bitlocker
    Assert-True ($b.status -eq 'unavailable') "status was $($b.status)"
    Assert-True ($b.error -like '*Home*') 'error does not mention Home'
}
Test-Case 'defender-off: defender ok, antivirus_enabled false' {
    $r = Invoke-Run 'defender-off'; Assert-SchemaValid $r.Text; $d = $r.Scan.protection.defender
    Assert-True ($d.status -eq 'ok') "status was $($d.status)"
    Assert-True ($d.antivirus_enabled -eq $false) 'antivirus_enabled not false'
}
Test-Case 'stale-patches: days_since_latest_hotfix is at least 75' {
    $r = Invoke-Run 'stale-patches'; Assert-SchemaValid $r.Text; $s = $r.Scan
    Assert-True ($s.patch.status -eq 'ok') "patch status was $($s.patch.status)"
    Assert-True ($s.patch.days_since_latest_hotfix -ge 75) "days was $($s.patch.days_since_latest_hotfix)"
}
Test-Case 'non-admin: admin-only fields null, all statuses ok' {
    $r = Invoke-Run 'non-admin'; Assert-SchemaValid $r.Text; $s = $r.Scan
    Assert-True ($s.host.is_admin -eq $false) 'is_admin not false'
    Assert-True ($null -eq $s.backup.shadow_copy_count) 'shadow_copy_count not null'
    Assert-True ($null -eq $s.recovery.restore_point_count) 'restore_point_count not null'
    Assert-True ($null -eq $s.backup.windows_backup_last_success) 'windows_backup_last_success not null'
    Assert-True ($null -eq $s.recovery.winre_enabled) 'winre_enabled not null'
    Assert-True ($null -eq $s.recovery.latest_restore_point) 'latest_restore_point not null'
    $st = Get-AllStatuses $s
    foreach ($k in $st.Keys) { Assert-True ($st[$k] -eq 'ok') "$k status $($st[$k])" }
}
Test-Case 'probe-throws: software failed, every other section ok' {
    $r = Invoke-Run 'probe-throws'; Assert-SchemaValid $r.Text; $s = $r.Scan
    $st = Get-AllStatuses $s
    Assert-True ($st['software'] -eq 'failed') "software status was $($st['software'])"
    foreach ($k in $st.Keys) { if ($k -ne 'software') { Assert-True ($st[$k] -eq 'ok') "$k status $($st[$k])" } }
}
# reads this PC, read-only: -DryRun, no mock. Asserts shape and statuses only; real values are never printed.
Test-Case 'no mock: all sections, shape and statuses (reads this PC, read-only)' {
    $r = Invoke-Run $null
    Assert-AllSections $r.Scan
    Assert-True ($r.Scan.host.is_admin -is [bool]) 'is_admin not bool'
    Assert-True ($r.Scan.host.hostname_hash -match '^sha256:[0-9a-f]{64}$') 'hostname_hash shape'
    Assert-SchemaValid $r.Text
}

Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
