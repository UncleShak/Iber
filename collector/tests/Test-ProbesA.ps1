# Phase 3 tests for probes\Host.ps1 and probes\Protection.ps1 (manual 3.5, 3.6, 0.9). In-process; every reader is faked.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'lib\Common.ps1')
foreach ($p in @('Host.ps1', 'Protection.ps1')) {
    $f = Join-Path $root ('probes\' + $p)
    if (Test-Path $f) { . $f }
}

$script:passed = 0
$script:failed = 0

$readerNames = @('Read-AgOsCaption','Read-AgOsBuild','Read-AgEdition','Read-AgMpStatus','Read-AgMpPreference',
    'Read-AgServiceStatus','Read-AgServices','Read-AgSecurityCenterAv','Read-AgBitLocker','Read-AgBitLockerCom',
    'Read-AgCfaRegistry','Read-AgAsrRegistry','Read-AgHotFix','Read-AgPendingReboot','Read-AgUninstallKeys',
    'Read-AgFileHistory','Read-AgShellFolders','Read-AgBackupEvent','Read-AgShadowCopies','Read-AgReagentc',
    'Read-AgSystemRestore','Read-AgRestorePoints','Read-AgPsVersion','Read-AgComputerName','Read-AgHasBitLockerCmdlet',
    'Test-AgAdmin')
$origDefs = @{}
foreach ($n in $readerNames) {
    $c = Get-Command -Name $n -CommandType Function -ErrorAction SilentlyContinue
    $origDefs[$n] = if ($null -ne $c) { $c.ScriptBlock.ToString() } else { '' }
}

function Set-Fake([string]$Name, [scriptblock]$Body) { Set-Item -Path ('function:script:' + $Name) -Value $Body }
function Set-FakeValue([string]$Name, $Value) { Set-Fake $Name ({ $Value }.GetNewClosure()) }
function Set-FakeThrow([string]$Name) { Set-Fake $Name { throw 'boom at C:\Users\bob\secret\file.txt' } }
function Reset-Fakes {
    foreach ($n in $readerNames) { Set-Fake $n { throw 'REAL READER CALLED' } }
    Set-FakeValue 'Read-AgComputerName' 'SECRET-PC'
}
function Test-Case([string]$Name, [scriptblock]$Body) {
    try {
        Reset-Fakes
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
function Get-Host6 { Get-AgHost }
function Get-MpFake([bool]$Av = $true, [string]$Mode = 'Normal') {
    [pscustomobject]@{ AntivirusEnabled = $Av; RealTimeProtectionEnabled = $true; IsTamperProtected = $true
        AntivirusSignatureAge = [uint32]2; AMRunningMode = $Mode }
}
function Set-HealthyDefender { Set-FakeValue 'Read-AgMpStatus' (Get-MpFake); Set-FakeValue 'Read-AgSecurityCenterAv' @('Windows Defender') }
function Get-CfaMode($code) {
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{ EnableControlledFolderAccess = $code })
    (Get-AgCfa)['mode']
}

# ---------- Guard: no real reader in play ----------
Test-Case 'Fakes replace every original reader' {
    foreach ($n in $readerNames) {
        $c = Get-Command -Name $n -CommandType Function
        Assert-True ($c.ScriptBlock.ToString() -ne $origDefs[$n]) "$n is still the original"
    }
    Assert-True ($origDefs['Read-AgPsVersion'] -ne '') 'Read-AgPsVersion missing from Common.ps1'
    Assert-True ($origDefs['Read-AgComputerName'] -ne '') 'Read-AgComputerName missing from Common.ps1'
    Assert-True ($origDefs['Read-AgHasBitLockerCmdlet'] -ne '') 'Read-AgHasBitLockerCmdlet missing from Common.ps1'
}

# ---------- Host ----------
function Set-HostFakes {
    Set-FakeValue 'Read-AgOsCaption' 'Microsoft Windows 11 Pro'
    Set-FakeValue 'Read-AgOsBuild' '22631'
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgPsVersion' '5.1.22621.4391'
}
Test-Case 'Host: six fields with the right types' {
    Set-HostFakes
    $h = Get-Host6
    Assert-True ($h['is_admin'] -is [bool]) 'is_admin not bool'
    Assert-True ($h['os_build'] -is [string] -and $h['os_build'] -match '^\d+$') 'os_build not digits'
    Assert-True ($h['hostname_hash'] -match '^sha256:[0-9a-f]{64}$') 'hash format'
    Assert-True ($h['hostname_hash'] -notmatch 'SECRET') 'hash leaks name'
    Assert-True ($h['os_caption'] -eq 'Microsoft Windows 11 Pro' -and $h['os_edition'] -eq 'Professional' -and $h['ps_version'] -eq '5.1.22621.4391') 'values'
    Assert-True ($h.Count -eq 6) 'field count'
}
Test-Case 'Host: fields in schema order' {
    Set-HostFakes
    $k = @((Get-Host6).Keys) -join ','
    Assert-True ($k -eq 'hostname_hash,os_caption,os_build,os_edition,is_admin,ps_version') "order was $k"
}
Test-Case 'Host: a throwing reader propagates' {
    Set-HostFakes
    Set-FakeThrow 'Read-AgOsBuild'
    $threw = $false
    try { [void](Get-Host6) } catch { $threw = $true }
    Assert-True $threw 'exception was swallowed'
}

# ---------- Defender ----------
Test-Case 'Defender: normal' {
    Set-HealthyDefender
    $d = Get-AgDefender
    Assert-True ($d['status'] -eq 'ok' -and $null -eq $d['error']) 'status'
    Assert-True ($d['antivirus_enabled'] -eq $true -and $d['realtime_enabled'] -eq $true -and $d['tamper_protected'] -eq $true) 'bools'
    Assert-True ($d['signature_age_days'] -is [int] -and $d['signature_age_days'] -eq 2) 'age not int'
    Assert-True ($null -eq $d['third_party_av']) 'third_party_av should be null'
}
Test-Case 'Defender: passive mode with third-party AV' {
    Set-FakeValue 'Read-AgMpStatus' (Get-MpFake $false 'Passive Mode')
    Set-FakeValue 'Read-AgSecurityCenterAv' @('Windows Defender', 'Contoso Shield')
    $d = Get-AgDefender
    Assert-True ($d['status'] -eq 'ok') 'status'
    Assert-True ($d['antivirus_enabled'] -eq $false -and $d['realtime_enabled'] -eq $true -and $d['signature_age_days'] -eq 2) 'fields still read'
    Assert-True ($d['third_party_av'] -eq 'Contoso Shield') 'third_party_av'
}
Test-Case 'Defender: only Microsoft products listed means no third party' {
    Set-FakeValue 'Read-AgMpStatus' (Get-MpFake)
    Set-FakeValue 'Read-AgSecurityCenterAv' @('Windows Defender', 'Microsoft Defender Antivirus')
    Assert-True ($null -eq (Get-AgDefender)['third_party_av']) 'expected null'
}
foreach ($svc in @('Stopped', $null)) {
    $label = if ($null -eq $svc) { 'missing' } else { $svc }
    Test-Case "Defender: status throws, WinDefend $label is a finding" {
        Set-FakeThrow 'Read-AgMpStatus'
        Set-FakeValue 'Read-AgServiceStatus' $svc
        Set-FakeValue 'Read-AgSecurityCenterAv' @()
        $d = Get-AgDefender
        Assert-True ($d['status'] -eq 'ok' -and $null -eq $d['error']) 'status should be ok'
        Assert-True ($d['antivirus_enabled'] -eq $false -and $d['realtime_enabled'] -eq $false) 'should be false'
        Assert-True ($null -eq $d['tamper_protected'] -and $null -eq $d['signature_age_days'] -and $null -eq $d['third_party_av']) 'others null'
    }
}
Test-Case 'Defender: status throws while WinDefend Running is failed, error clean' {
    Set-FakeThrow 'Read-AgMpStatus'
    Set-FakeValue 'Read-AgServiceStatus' 'Running'
    Set-FakeValue 'Read-AgSecurityCenterAv' @()
    $d = Get-AgDefender
    Assert-True ($d['status'] -eq 'failed') "status was $($d['status'])"
    Assert-True ($d['error'] -notmatch '[A-Za-z]:\\' -and $d['error'] -notmatch 'bob') "error leaks: $($d['error'])"
}

Test-Case 'Defender: signature age uint32 max (never) gives null, rest kept' {
    $mp = Get-MpFake
    $mp.AntivirusSignatureAge = [uint32]4294967295
    Set-FakeValue 'Read-AgMpStatus' $mp
    Set-FakeValue 'Read-AgSecurityCenterAv' @()
    $d = Get-AgDefender
    Assert-True ($d['status'] -eq 'ok') "status was $($d['status'])"
    Assert-True ($null -eq $d['signature_age_days']) 'age should be null'
    Assert-True ($d['antivirus_enabled'] -eq $true -and $d['realtime_enabled'] -eq $true -and $d['tamper_protected'] -eq $true) 'other fields lost'
}
Test-Case 'Defender: empty or blank displayName is no product' {
    Set-FakeValue 'Read-AgMpStatus' (Get-MpFake)
    Set-FakeValue 'Read-AgSecurityCenterAv' @('', '   ', 'Windows Defender')
    Assert-True ($null -eq (Get-AgDefender)['third_party_av']) 'blank name taken as product'
}
Test-Case 'Defender: third-party name without the letter s is kept' {
    Set-FakeValue 'Read-AgMpStatus' (Get-MpFake)
    Set-FakeValue 'Read-AgSecurityCenterAv' @('Windows Defender', 'Avira')
    Assert-True ((Get-AgDefender)['third_party_av'] -eq 'Avira') "third_party_av was '$((Get-AgDefender)['third_party_av'])'"
}
Test-Case 'Host: null or non-digit build throws OS build unreadable' {
    foreach ($bad in @($null, 'abc', '')) {
        Set-HostFakes
        Set-FakeValue 'Read-AgOsBuild' $bad
        $msg = $null
        try { [void](Get-Host6) } catch { $msg = $_.Exception.Message }
        Assert-True ($msg -ceq 'OS build unreadable') "build '$bad' gave message '$msg'"
    }
}
Test-Case 'ASR: registry names that are not 36-char GUIDs are left out' {
    Set-FakeThrow 'Read-AgMpPreference'
    Set-FakeValue 'Read-AgAsrRegistry' ([ordered]@{ 'd4f940ab-401b-4efc-aadc-ad5f3c50688a' = 1; '{3b576869-a4ec-4529-8536-b80a7769e899}' = 1; 'junk value' = 2; '75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84' = 6 })
    $r = @((Get-AgAsr)['rules'])
    Assert-True ($r.Count -eq 2 -and $r[0]['id'] -eq 'd4f940ab-401b-4efc-aadc-ad5f3c50688a' -and $r[1]['id'] -eq '75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84') "got $($r.Count) rules"
}
Test-Case 'BitLocker: 99.6 percent is not rounded up to 100' {
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgHasBitLockerCmdlet' $true
    Set-FakeValue 'Read-AgBitLocker' ([pscustomobject]@{ ProtectionStatus = 'On'; EncryptionPercentage = 99.6; EncryptionMethod = 'XtsAes128' })
    $p = (Get-AgBitLocker)['os_volume_encryption_pct']
    Assert-True ($p -is [int] -and $p -eq 99) "got $p"
}

# ---------- CFA ----------
foreach ($pair in @(@(0, 'disabled'), @(1, 'enabled'), @(2, 'audit'), @(3, 'enabled'), @(4, 'audit'))) {
    $code = $pair[0]; $want = $pair[1]
    Test-Case "CFA: code $code maps to $want" {
        $m = Get-CfaMode $code
        Assert-True ($m -eq $want) "got $m"
    }
}
Test-Case 'CFA: unknown code gives null mode' {
    Assert-True ($null -eq (Get-CfaMode 9)) 'expected null'
}
Test-Case 'CFA: preference throws, registry fallback used' {
    Set-FakeThrow 'Read-AgMpPreference'
    Set-FakeValue 'Read-AgCfaRegistry' 1
    $c = Get-AgCfa
    Assert-True ($c['status'] -eq 'ok' -and $c['mode'] -eq 'enabled') "got $($c['status']) $($c['mode'])"
}
Test-Case 'CFA: preference has no value, registry fallback used' {
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{ EnableControlledFolderAccess = $null })
    Set-FakeValue 'Read-AgCfaRegistry' 2
    Assert-True ((Get-AgCfa)['mode'] -eq 'audit') 'fallback not used'
}
Test-Case 'CFA: both empty gives null mode, status ok' {
    Set-FakeThrow 'Read-AgMpPreference'
    Set-FakeValue 'Read-AgCfaRegistry' $null
    $c = Get-AgCfa
    Assert-True ($c['status'] -eq 'ok' -and $null -eq $c['mode']) 'expected ok and null'
}

# ---------- ASR ----------
$g1 = 'd4f940ab-401b-4efc-aadc-ad5f3c50688a'
$g2 = '3b576869-a4ec-4529-8536-b80a7769e899'
$g3 = '75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84'
$g4 = '92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b'
$g5 = '9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2'
$g6 = 'be9ba2d9-53ea-4cdc-84e5-9b1eeee46550'
Test-Case 'ASR: codes 0 1 2 5 6 mapped, 99 left out' {
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{
        AttackSurfaceReductionRules_Ids = @($g1, $g2, $g3, $g4, $g5, $g6)
        AttackSurfaceReductionRules_Actions = @(0, 1, 2, 5, 6, 99) })
    $a = Get-AgAsr
    Assert-True ($a['status'] -eq 'ok') 'status'
    $r = @($a['rules'])
    Assert-True ($r.Count -eq 5) "count was $($r.Count)"
    $exp = @('off', 'block', 'audit', 'off', 'warn')
    $ids = @($g1, $g2, $g3, $g4, $g5)
    for ($i = 0; $i -lt 5; $i++) {
        Assert-True ($r[$i]['id'] -eq $ids[$i] -and $r[$i]['action'] -eq $exp[$i]) "rule $i wrong"
    }
}
Test-Case 'ASR: a single rule stays an array through ConvertTo-Json' {
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{
        AttackSurfaceReductionRules_Ids = @($g1); AttackSurfaceReductionRules_Actions = @(1) })
    $a = Get-AgAsr
    $json = ConvertTo-Json -InputObject $a -Depth 8
    Assert-True ($json -match '"rules":\s*\[') "rules not an array: $json"
}
Test-Case 'ASR: empty Ids and Actions use registry fallback' {
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{
        AttackSurfaceReductionRules_Ids = @(); AttackSurfaceReductionRules_Actions = @() })
    Set-FakeValue 'Read-AgAsrRegistry' ([ordered]@{ $g1 = 1; $g2 = 2 })
    $r = @((Get-AgAsr)['rules'])
    Assert-True ($r.Count -eq 2 -and $r[0]['action'] -eq 'block' -and $r[1]['action'] -eq 'audit') 'fallback wrong'
}
Test-Case 'ASR: both empty gives rules empty, status ok' {
    Set-FakeThrow 'Read-AgMpPreference'
    Set-FakeValue 'Read-AgAsrRegistry' ([ordered]@{})
    $a = Get-AgAsr
    $json = ConvertTo-Json -InputObject $a -Depth 8
    Assert-True ($a['status'] -eq 'ok' -and @($a['rules']).Count -eq 0) 'expected ok and empty'
    Assert-True ($json -match '"rules":\s*\[\s*\]') "rules not []: $json"
}

# ---------- BitLocker ----------
foreach ($ed in @('Core', 'CoreSingleLanguage')) {
    Test-Case "BitLocker: edition $ed is unavailable (Home)" {
        Set-FakeValue 'Read-AgEdition' $ed
        $b = Get-AgBitLocker
        Assert-True ($b['status'] -eq 'unavailable') "status was $($b['status'])"
        Assert-True ($b['error'] -ceq 'BitLocker management not available on Windows Home') "error was $($b['error'])"
    }
}
foreach ($pair in @(@('On', 'on'), @('Off', 'off'))) {
    $in = $pair[0]; $want = $pair[1]
    Test-Case "BitLocker: admin with cmdlet, ProtectionStatus $in" {
        Set-FakeValue 'Read-AgEdition' 'Professional'
        Set-FakeValue 'Test-AgAdmin' $true
        Set-FakeValue 'Read-AgHasBitLockerCmdlet' $true
        Set-FakeValue 'Read-AgBitLocker' ([pscustomobject]@{ ProtectionStatus = $in; EncryptionPercentage = 100; EncryptionMethod = 'XtsAes128' })
        $b = Get-AgBitLocker
        Assert-True ($b['status'] -eq 'ok' -and $b['os_volume_protection'] -eq $want) 'protection'
        Assert-True ($b['os_volume_encryption_pct'] -is [int] -and $b['os_volume_encryption_pct'] -eq 100) 'pct not int'
        Assert-True ($b['encryption_method'] -is [string] -and $b['encryption_method'] -eq 'XtsAes128') 'method'
    }
}
foreach ($pair in @(@(1, 'ok', 'on'), @(2, 'ok', 'off'), @(3, 'ok', 'off'), @(7, 'unavailable', $null))) {
    $code = $pair[0]; $st = $pair[1]; $want = $pair[2]
    Test-Case "BitLocker: non-admin COM $code" {
        Set-FakeValue 'Read-AgEdition' 'Professional'
        Set-FakeValue 'Test-AgAdmin' $false
        Set-FakeValue 'Read-AgBitLockerCom' $code
        $b = Get-AgBitLocker
        Assert-True ($b['status'] -eq $st) "status was $($b['status'])"
        Assert-True ($b['os_volume_protection'] -eq $want) "protection was $($b['os_volume_protection'])"
    }
}
Test-Case 'BitLocker: non-admin and COM null is unavailable, needs admin' {
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $false
    Set-FakeValue 'Read-AgBitLockerCom' $null
    $b = Get-AgBitLocker
    Assert-True ($b['status'] -eq 'unavailable' -and $b['error'] -ceq 'Requires administrator rights') "got $($b['status']) $($b['error'])"
}
Test-Case 'BitLocker: admin but cmdlet missing falls back to COM' {
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgHasBitLockerCmdlet' $false
    Set-FakeValue 'Read-AgBitLockerCom' 1
    $b = Get-AgBitLocker
    Assert-True ($b['status'] -eq 'ok' -and $b['os_volume_protection'] -eq 'on') 'COM fallback not used'
}
Test-Case 'BitLocker: reader throws gives failed' {
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgHasBitLockerCmdlet' $true
    Set-FakeThrow 'Read-AgBitLocker'
    $b = Get-AgBitLocker
    Assert-True ($b['status'] -eq 'failed') "status was $($b['status'])"
    Assert-True ($b['error'] -notmatch '[A-Za-z]:\\' -and $b['error'] -notmatch 'bob') 'error leaks'
}

# ---------- Shape ----------
function Set-ProtectionFakes {
    Set-HealthyDefender
    Set-FakeValue 'Read-AgMpPreference' ([pscustomobject]@{ EnableControlledFolderAccess = 1
        AttackSurfaceReductionRules_Ids = @($g1); AttackSurfaceReductionRules_Actions = @(1) })
    Set-FakeValue 'Read-AgEdition' 'Professional'
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgHasBitLockerCmdlet' $true
    Set-FakeValue 'Read-AgBitLocker' ([pscustomobject]@{ ProtectionStatus = 'On'; EncryptionPercentage = 100; EncryptionMethod = 'XtsAes128' })
}
Test-Case 'Protection: keys and sub-block heads' {
    Set-ProtectionFakes
    $p = Get-AgProtection
    Assert-True ((@($p.Keys) -join ',') -eq 'bitlocker,defender,cfa,asr') "keys were $(@($p.Keys) -join ',')"
    foreach ($k in $p.Keys) {
        Assert-True ((@($p[$k].Keys)[0..1] -join ',') -eq 'status,error') "$k does not start with status,error"
        Assert-True ($p[$k]['status'] -eq 'ok') "$k status $($p[$k]['status'])"
    }
}
Test-Case 'Protection: a failing sub-probe does not stop the others' {
    Set-ProtectionFakes
    Set-FakeThrow 'Read-AgBitLocker'
    $p = Get-AgProtection
    Assert-True ($p['bitlocker']['status'] -eq 'failed') 'bitlocker should fail'
    Assert-True ($p['defender']['status'] -eq 'ok' -and $p['cfa']['status'] -eq 'ok' -and $p['asr']['status'] -eq 'ok') 'others should be ok'
}

# ---------- Read-only guard ----------
Test-Case 'Test-ReadOnly.ps1 prints READ-ONLY OK' {
    $out = & powershell.exe -NoProfile -File (Join-Path $PSScriptRoot 'Test-ReadOnly.ps1') 2>&1 | Out-String
    Assert-True ($out -match 'READ-ONLY OK') ('guard output: ' + (($out -split "`r?`n")[0..2] -join ' | '))
}

Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
