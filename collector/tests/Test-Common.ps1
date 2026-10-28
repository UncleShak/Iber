# Phase 1 tests for lib\Common.ps1 and lib\Allowlist.ps1 (manual 3.4, 3.7, 3.8)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$common = Join-Path $root 'lib\Common.ps1'
$allow  = Join-Path $root 'lib\Allowlist.ps1'
if (Test-Path $common) { . $common }
if (Test-Path $allow)  { . $allow }

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

$readers = @('Read-AgOsCaption','Read-AgOsBuild','Read-AgEdition','Read-AgMpStatus','Read-AgMpPreference',
    'Read-AgServiceStatus','Read-AgServices','Read-AgSecurityCenterAv','Read-AgBitLocker','Read-AgBitLockerCom',
    'Read-AgCfaRegistry','Read-AgAsrRegistry','Read-AgHotFix','Read-AgPendingReboot','Read-AgUninstallKeys',
    'Read-AgFileHistory','Read-AgShellFolders','Read-AgBackupEvent','Read-AgShadowCopies','Read-AgReagentc',
    'Read-AgSystemRestore','Read-AgRestorePoints')

$expectedAllow = @('Get-CimInstance','Get-ItemProperty','Get-ChildItem','Get-Service','Get-HotFix',
    'Get-MpComputerStatus','Get-MpPreference','Get-BitLockerVolume','Get-ComputerRestorePoint','Get-WinEvent',
    'Get-Command','Get-Random','Get-Culture','Test-Path','Where-Object','ForEach-Object','Sort-Object',
    'Select-Object','Resolve-Path','ConvertTo-Json','Write-Error','Write-Output','New-Object','reagentc.exe')

Test-Case 'IsoUtc null returns null' {
    $r = ConvertTo-IsoUtc $null
    Assert-True ($null -eq $r) 'expected $null'
}
Test-Case 'IsoUtc known date' {
    $d = New-Object DateTime 2026, 3, 5, 14, 30, 0, ([DateTimeKind]::Local)
    $exp = $d.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ', [Globalization.CultureInfo]::InvariantCulture)
    $r = ConvertTo-IsoUtc $d
    Assert-True ($r -eq $exp) "expected $exp got $r"
}
Test-Case 'Invoke-Probe ok' {
    $tpl = [ordered]@{ alpha = $null; beta = $null; gamma = $null }
    $r = Invoke-Probe -Template $tpl -Body { @{ alpha = 1; beta = 'two' } }
    Assert-True ($r['status'] -eq 'ok') 'status not ok'
    Assert-True ($null -eq $r['error']) 'error not null'
    Assert-True ($r['alpha'] -eq 1 -and $r['beta'] -eq 'two') 'data not merged'
    Assert-True ($r.Contains('gamma') -and $null -eq $r['gamma']) 'gamma missing or not null'
    $keys = @($r.Keys) -join ','
    Assert-True ($keys -eq 'status,error,alpha,beta,gamma') "key order was $keys"
}
Test-Case 'Invoke-Probe unavailable' {
    $tpl = [ordered]@{ alpha = $null; beta = $null }
    $r = Invoke-Probe -Template $tpl -Body { throw ([AgUnavailable]::new('Requires administrator rights')) }
    Assert-True ($r['status'] -eq 'unavailable') "status was $($r['status'])"
    Assert-True ($r['error'] -eq 'Requires administrator rights') "error was $($r['error'])"
    Assert-True ($r.Contains('alpha') -and $r.Contains('beta')) 'template keys missing'
}
Test-Case 'Invoke-Probe failed' {
    $tpl = [ordered]@{ alpha = $null }
    $r = Invoke-Probe -Template $tpl -Body { throw ([System.IO.IOException]::new('simulated')) }
    Assert-True ($r['status'] -eq 'failed') "status was $($r['status'])"
    Assert-True ($r['error'] -eq 'IOException: simulated') "error was $($r['error'])"
    $long = 'a' * 500
    $b2 = { throw ([System.IO.IOException]::new($long)) }.GetNewClosure()
    $r2 = Invoke-Probe -Template $tpl -Body $b2
    Assert-True ($r2['error'].Length -le 200) "length was $($r2['error'].Length)"
}
Test-Case 'Invoke-Probe failed scrubs sensitive text' {
    $tpl = [ordered]@{ alpha = $null }
    $msg = 'bad C:\Users\x\file.txt and \\server\share\f user ' + $env:USERNAME + ' host ' + $env:COMPUTERNAME + ' sid S-1-5-21-1-2-3-1001'
    $b3 = { throw ([System.IO.IOException]::new($msg)) }.GetNewClosure()
    $r = Invoke-Probe -Template $tpl -Body $b3
    $e = [string]$r['error']
    foreach ($bad in @('C:\Users\x', '\\server', 'S-1-5-21', $env:USERNAME, $env:COMPUTERNAME)) {
        if ($bad) { Assert-True ($e.IndexOf($bad, [StringComparison]::OrdinalIgnoreCase) -lt 0) 'sensitive text leaked' }
    }
    Assert-True ($e.Contains('<path>')) 'no <path> marker'
}
Test-Case 'ConvertTo-AgSafeError keeps plain text' {
    $t = 'Requires administrator rights'
    Assert-True ((ConvertTo-AgSafeError $t) -eq $t) 'text changed'
}
Test-Case 'IsoUtc fixed UTC input' {
    $d = [DateTime]::SpecifyKind([DateTime]'2026-11-14 16:42:07', 'Utc')
    $r = ConvertTo-IsoUtc $d
    Assert-True ($r -eq '2026-11-14T16:42:07Z') "got $r"
}
Test-Case 'IsoUtc ignores thread culture' {
    $old = [Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [Threading.Thread]::CurrentThread.CurrentCulture = 'th-TH'
        $d = [DateTime]::SpecifyKind([DateTime]'2026-11-14 16:42:07', 'Utc')
        $r = ConvertTo-IsoUtc $d
        Assert-True ($r -eq '2026-11-14T16:42:07Z') "got $r"
    } finally { [Threading.Thread]::CurrentThread.CurrentCulture = $old }
}
Test-Case 'IsoUtc rejects non-DateTime' {
    $threw = $false
    try { ConvertTo-IsoUtc 133000000000000000 | Out-Null } catch { $threw = $true }
    Assert-True $threw 'did not throw for a long'
}
Test-Case 'SafeError scrubs path with spaces in user name' {
    $e = ConvertTo-AgSafeError 'Access to C:\Users\John Smith\AppData\x denied'
    Assert-True ($e -notmatch 'John' -and $e -notmatch 'Smith') "leaked: $e"
}
Test-Case 'SafeError scrubs path variants' {
    foreach ($t in @('C:/Users/jsmith/x', 'file:///C:/Users/jsmith/x', '\?\C:\Users\jsmith\x', '\srv\share\a b')) {
        $e = ConvertTo-AgSafeError ("failed " + $t)
        Assert-True ($e -notmatch 'jsmith' -and $e -notmatch 'srv') "leaked from '$t': $e"
    }
}
Test-Case 'SafeError scrubs any SID' {
    $e = ConvertTo-AgSafeError 'owner S-1-12-1-111-222 here'
    Assert-True ($e -notmatch '111' -and $e -notmatch '222') "leaked: $e"
}
Test-Case 'SafeError redacts whole-word user name only' {
    $u = $env:USERNAME
    $e1 = ConvertTo-AgSafeError ("hello $u there")
    Assert-True ($e1 -notmatch [regex]::Escape($u)) "not redacted: $e1"
    $s = 'x' + $u + 'y'
    $e2 = ConvertTo-AgSafeError $s
    Assert-True ($e2 -eq $s) "over-redacted: $e2"
}
Test-Case 'Get-AgHash format and behaviour' {
    $h = Get-AgHash 'MY-PC'
    Assert-True ($h -match '^sha256:[0-9a-f]{64}$') "bad format $h"
    Assert-True ($h -eq (Get-AgHash 'MY-PC')) 'not deterministic'
    Assert-True ($h -ne (Get-AgHash 'OTHER-PC')) 'collision'
    Assert-True (-not $h.Contains('MY-PC')) 'contains input'
}
Test-Case 'Write-ScanJson file output' {
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $scan = [ordered]@{
            schema_version = '1.0.0'
            patch = [ordered]@{ hotfixes = @( [ordered]@{ kb = 'KB1'; installed_on = '2026-01-01' } ) }
            protection = [ordered]@{ asr = [ordered]@{ rules = @( [ordered]@{ id = 'x'; action = 'block' } ) } }
        }
        Write-ScanJson -Scan $scan -Path $p
        $b = [IO.File]::ReadAllBytes($p)
        Assert-True (-not ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)) 'BOM present'
        $txt = [IO.File]::ReadAllText($p)
        $o = $txt | ConvertFrom-Json
        Assert-True ($o.patch.hotfixes -is [array]) 'hotfixes collapsed'
        Assert-True ($o.patch.hotfixes[0].kb -eq 'KB1') 'hotfix content wrong'
        Assert-True ($o.protection.asr.rules -is [array]) 'rules collapsed'
        Assert-True ($o.protection.asr.rules[0].action -eq 'block') '3-level nesting broken'
        Assert-True (-not $txt.Contains('System.Collections')) 'System.Collections in output'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Write-ScanJson DryRun' {
    $dir = New-TempDir
    try {
        $p = Join-Path $dir 'scan.json'
        $r = Write-ScanJson -Scan ([ordered]@{ a = 1 }) -Path $p -DryRun
        Assert-True (-not [IO.File]::Exists($p)) 'file was created'
        $txt = (@($r) -join "`n")
        Assert-True (($txt | ConvertFrom-Json).a -eq 1) 'returned text not JSON'
    } finally { [IO.Directory]::Delete($dir, $true) }
}
Test-Case 'Test-AgAdmin returns bool' {
    $r = Test-AgAdmin
    Assert-True ($r -is [bool]) 'not a bool'
}
Test-Case 'All Read-Ag readers exist' {
    $missing = @()
    foreach ($n in $readers) {
        if (-not (Get-Command -Name $n -CommandType Function -ErrorAction SilentlyContinue)) { $missing += $n }
    }
    Assert-True ($missing.Count -eq 0) ("missing: " + ($missing -join ', '))
}
Test-Case 'Mock override of Read-AgEdition wins' {
    Assert-True ([bool](Get-Command -Name 'Read-AgEdition' -CommandType Function -ErrorAction SilentlyContinue)) 'Read-AgEdition not defined'
    . ([scriptblock]::Create("function Read-AgEdition { 'Core' }"))
    Assert-True ((Read-AgEdition) -eq 'Core') 'override did not win'
}
Test-Case 'Allowlist has exactly the 24 names' {
    Assert-True ($null -ne $AgAllowedCommands) '$AgAllowedCommands not defined'
    $a = @($AgAllowedCommands | Sort-Object)
    $e = @($expectedAllow | Sort-Object)
    $missing = @($e | Where-Object { $a -notcontains $_ })
    $extra = @($a | Where-Object { $e -notcontains $_ })
    Assert-True ($missing.Count -eq 0 -and $extra.Count -eq 0 -and $a.Count -eq 24) ("missing: $($missing -join ',') extra: $($extra -join ',')")
}
Test-Case 'Every collector .ps1 has UTF-8 BOM' {
    $bad = @()
    foreach ($f in Get-ChildItem -Path $root -Recurse -Filter '*.ps1') {
        $b = [IO.File]::ReadAllBytes($f.FullName)
        if ($b.Length -eq 0) { continue }
        if (-not ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)) { $bad += $f.Name }
    }
    Assert-True ($bad.Count -eq 0) ("no BOM: " + ($bad -join ', '))
}

Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
