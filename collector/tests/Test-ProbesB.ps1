# Phase 4 tests for probes\Backup.ps1, Patch.ps1, Software.ps1, Recovery.ps1 (manual 3.5, 3.6). In-process; every reader is faked.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'lib\Common.ps1')
foreach ($p in @('Backup.ps1', 'Patch.ps1', 'Software.ps1', 'Recovery.ps1')) {
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

function Set-Fake([string]$Name, [scriptblock]$Body) { Set-Item -Path ('function:script:' + $Name) -Value $Body }
function Set-FakeValue([string]$Name, $Value) { Set-Fake $Name ({ $Value }.GetNewClosure()) }
function Set-FakeThrow([string]$Name) { Set-Fake $Name { throw 'boom at C:\Users\bob\secret\file.txt' } }
function Reset-Fakes { foreach ($n in $readerNames) { Set-Fake $n { throw 'REAL READER CALLED' } } }
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
function Get-Keys($d) { @($d.Keys) -join ',' }
function New-Svc([string]$Name, [string]$Display = '', [string]$Start = 'Automatic') {
    [pscustomobject]@{ Name = $Name; DisplayName = $Display; Status = 'Running'; StartType = $Start }
}
$today = [DateTime]::UtcNow.Date

# =============== Backup ===============
function Set-BackupFakes {
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgServices' @((New-Svc 'fhsvc' 'File History Service' 'Manual'))
    Set-FakeValue 'Read-AgFileHistory' ([ordered]@{ config_exists = $true; protected_up_to_raw = ([DateTime]::new(2026, 3, 10, 8, 0, 0, [DateTimeKind]::Utc)).ToFileTimeUtc() })
    Set-FakeValue 'Read-AgBackupEvent' ([pscustomobject]@{ TimeCreated = [DateTime]::new(2026, 3, 9, 7, 30, 0, [DateTimeKind]::Utc) })
    Set-FakeValue 'Read-AgShellFolders' ([ordered]@{ Desktop = 'C:\Users\x\Desktop'; Personal = 'C:\Users\x\Documents'; 'My Pictures' = 'C:\Users\x\Pictures' })
    Set-FakeValue 'Read-AgShadowCopies' @(1, 2, 3)
}
Test-Case 'Backup: healthy admin, keys in schema order, types right' {
    Set-BackupFakes
    $b = Get-AgBackup
    Assert-True ((Get-Keys $b) -eq 'status,error,file_history_enabled,file_history_last_backup,windows_backup_last_success,onedrive_kfm_folders,shadow_copy_count,third_party_agents') "keys: $(Get-Keys $b)"
    Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['error']) 'status'
    Assert-True ($b['file_history_enabled'] -eq $true) 'file_history_enabled'
    Assert-True ($b['file_history_last_backup'] -ceq '2026-03-10T08:00:00Z') "last backup was $($b['file_history_last_backup'])"
    Assert-True ($b['windows_backup_last_success'] -ceq '2026-03-09T07:30:00Z') "event was $($b['windows_backup_last_success'])"
    Assert-True ($b['shadow_copy_count'] -is [int] -and $b['shadow_copy_count'] -eq 3) 'shadow count'
}
Test-Case 'Backup: File History service Disabled gives false' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgServices' @((New-Svc 'fhsvc' 'File History Service' 'Disabled'))
    Assert-True ((Get-AgBackup)['file_history_enabled'] -eq $false) 'expected false'
}
Test-Case 'Backup: no config file gives enabled false and last backup null' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgFileHistory' ([ordered]@{ config_exists = $false; protected_up_to_raw = $null })
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'ok' -and $b['file_history_enabled'] -eq $false -and $null -eq $b['file_history_last_backup']) 'expected ok/false/null'
}
foreach ($raw in @($null, 0)) {
    Test-Case "Backup: ProtectedUpToTime raw '$raw' gives null" {
        Set-BackupFakes
        Set-FakeValue 'Read-AgFileHistory' ([ordered]@{ config_exists = $true; protected_up_to_raw = $raw })
        $b = Get-AgBackup
        Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['file_history_last_backup']) 'expected null'
    }
}
Test-Case 'Backup: no backup event (empty result) gives null, ok' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgBackupEvent' $null
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['windows_backup_last_success']) 'expected null/ok'
}
Test-Case 'Backup: another event-log error is failed, error clean' {
    Set-BackupFakes
    Set-FakeThrow 'Read-AgBackupEvent'
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'failed') "status was $($b['status'])"
    Assert-True ($b['error'] -notmatch '[A-Za-z]:\\' -and $b['error'] -notmatch 'bob') 'error leaks'
}
Test-Case 'Backup: non-admin nulls the admin fields and never calls their readers (P3)' {
    Set-BackupFakes
    Set-FakeValue 'Test-AgAdmin' $false
    Set-FakeThrow 'Read-AgBackupEvent'
    Set-FakeThrow 'Read-AgShadowCopies'
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['shadow_copy_count'] -and $null -eq $b['windows_backup_last_success']) "status $($b['status']) $($b['error'])"
    Assert-True ($b['file_history_enabled'] -eq $true) 'non-admin fields still read'
}
Test-Case 'Backup: OneDrive folders by friendly name, never paths' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgShellFolders' ([ordered]@{ Desktop = 'C:\Users\x\OneDrive\Desktop'; Personal = 'C:\Users\x\Documents'; 'My Pictures' = 'C:\Users\x\OneDrive - Contoso\Pictures' })
    $b = Get-AgBackup
    Assert-True ((@($b['onedrive_kfm_folders']) -join ',') -eq 'Desktop,Pictures') "got $(@($b['onedrive_kfm_folders']) -join ',')"
    $json = ConvertTo-Json -InputObject $b -Depth 8
    Assert-True ($json -notmatch '[A-Za-z]:\\\\') 'path in output'
}
Test-Case 'Backup: all three OneDrive folders map to Desktop,Documents,Pictures' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgShellFolders' ([ordered]@{ Desktop = 'C:\Users\x\OneDrive\Desktop'; Personal = 'C:\Users\x\OneDrive\Documents'; 'My Pictures' = 'C:\Users\x\OneDrive\Pictures' })
    Assert-True ((@((Get-AgBackup)['onedrive_kfm_folders']) -join ',') -eq 'Desktop,Documents,Pictures') 'mapping'
}
Test-Case 'Backup: one OneDrive folder and no folder stay arrays in JSON' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgShellFolders' ([ordered]@{ Desktop = 'C:\Users\x\OneDrive\Desktop'; Personal = 'D:\Docs'; 'My Pictures' = 'D:\Pics' })
    Assert-True ((ConvertTo-Json -InputObject (Get-AgBackup) -Depth 8) -match '"onedrive_kfm_folders":\s*\[') 'single not an array'
    Set-FakeValue 'Read-AgShellFolders' ([ordered]@{ Desktop = 'D:\a'; Personal = 'D:\b'; 'My Pictures' = 'D:\c' })
    Assert-True ((ConvertTo-Json -InputObject (Get-AgBackup) -Depth 8) -match '"onedrive_kfm_folders":\s*\[\s*\]') 'empty not []'
}
Test-Case 'Backup: third-party agents in P4 order, no duplicates, Name or DisplayName' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgServices' @(
        (New-Svc 'IDriveService' 'x'), (New-Svc 'svc1' 'Synology Active Backup for Business'), (New-Svc 'VeeamBackupSvc' 'Veeam Backup'),
        (New-Svc 'VeeamTransportSvc' 'Veeam Transport'), (New-Svc 'a2' 'Acronis Scheduler'), (New-Svc 'Spooler' 'Print Spooler'), (New-Svc 'fhsvc' 'File History' 'Manual'))
    $a = @((Get-AgBackup)['third_party_agents'])
    Assert-True (($a -join '|') -eq 'Veeam|Acronis|Synology Active Backup|IDrive') "got $($a -join '|')"
}
Test-Case 'Backup: all nine vendor names map' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgServices' @((New-Svc 'MacriumService'), (New-Svc 'BackblazeBzserv'), (New-Svc 'CarboniteService'), (New-Svc 'DattoBackup'), (New-Svc 'CrashPlanSvc'),
        (New-Svc 'VeeamX'), (New-Svc 'AcronisX'), (New-Svc 'q' 'Synology Active Backup'), (New-Svc 'IDriveX'))
    $a = @((Get-AgBackup)['third_party_agents']) -join '|'
    Assert-True ($a -eq 'Veeam|Acronis|Macrium|Backblaze|Carbonite|Datto|Synology Active Backup|CrashPlan|IDrive') "got $a"
}
Test-Case 'Backup: one agent stays an array in JSON; none is []' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgServices' @((New-Svc 'VeeamX'))
    Assert-True ((ConvertTo-Json -InputObject (Get-AgBackup) -Depth 8) -match '"third_party_agents":\s*\[') 'single not an array'
    Set-FakeValue 'Read-AgServices' @((New-Svc 'Spooler'))
    Assert-True ((ConvertTo-Json -InputObject (Get-AgBackup) -Depth 8) -match '"third_party_agents":\s*\[\s*\]') 'empty not []'
}

# =============== Patch ===============
function New-Hf([string]$Id, $On) { [pscustomobject]@{ HotFixID = $Id; InstalledOn = $On } }
Test-Case 'Patch: healthy, keys in schema order, newest first, top 10 of 12' {
    $h = @(); for ($i = 1; $i -le 12; $i++) { $h += (New-Hf ('KB50000{0:D2}' -f $i) ($today.AddDays(-10 * $i))) }
    Set-FakeValue 'Read-AgHotFix' $h
    Set-FakeValue 'Read-AgPendingReboot' $false
    $p = Get-AgPatch
    Assert-True ((Get-Keys $p) -eq 'status,error,hotfix_count,latest_hotfix_installed_on,days_since_latest_hotfix,hotfixes,pending_reboot') "keys: $(Get-Keys $p)"
    Assert-True ($p['status'] -eq 'ok' -and $p['hotfix_count'] -eq 12 -and $p['hotfix_count'] -is [int]) 'count'
    $hf = @($p['hotfixes'])
    Assert-True ($hf.Count -eq 10 -and $hf[0]['kb'] -eq 'KB5000001' -and $hf[0]['installed_on'] -ceq $today.AddDays(-10).ToString('yyyy-MM-dd')) 'top 10 / order'
    Assert-True ($p['latest_hotfix_installed_on'] -ceq $today.AddDays(-10).ToString('yyyy-MM-dd')) 'latest'
    Assert-True ($p['days_since_latest_hotfix'] -is [int] -and $p['days_since_latest_hotfix'] -eq 10) "days $($p['days_since_latest_hotfix'])"
    Assert-True ($p['pending_reboot'] -eq $false) 'pending_reboot'
}
Test-Case 'Patch: IDs not matching ^KB\d+$ are left out but counted (P2)' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $today.AddDays(-5)), (New-Hf 'Update 1' $today.AddDays(-2)), (New-Hf 'kb123' $today.AddDays(-3)), (New-Hf 'KB12x' $today.AddDays(-4)))
    Set-FakeValue 'Read-AgPendingReboot' $true
    $p = Get-AgPatch
    Assert-True ($p['hotfix_count'] -eq 4) "count $($p['hotfix_count'])"
    Assert-True ((@($p['hotfixes']) | ForEach-Object { $_['kb'] }) -join ',' -ceq 'KB5000001') 'only the valid KB should be listed'
}
Test-Case 'Patch: hotfixes with null InstalledOn are dropped from the list' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $today.AddDays(-5)), (New-Hf 'KB5000002' $null))
    Set-FakeValue 'Read-AgPendingReboot' $false
    $p = Get-AgPatch
    Assert-True ($p['status'] -eq 'ok' -and $p['hotfix_count'] -eq 2 -and @($p['hotfixes']).Count -eq 1) 'drop nulls, count all'
}
Test-Case 'Patch: all InstalledOn null with count > 0 is unavailable' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $null), (New-Hf 'KB5000002' $null))
    Set-FakeValue 'Read-AgPendingReboot' $false
    $p = Get-AgPatch
    Assert-True ($p['status'] -eq 'unavailable' -and $p['error'] -ceq 'Update dates unreadable on this PC') "got $($p['status']) $($p['error'])"
}
Test-Case 'Patch: no hotfixes is ok with count 0 and nulls' {
    Set-FakeValue 'Read-AgHotFix' @()
    Set-FakeValue 'Read-AgPendingReboot' $false
    $p = Get-AgPatch
    Assert-True ($p['status'] -eq 'ok' -and $p['hotfix_count'] -eq 0 -and $null -eq $p['latest_hotfix_installed_on'] -and $null -eq $p['days_since_latest_hotfix']) 'zero case'
    Assert-True ((ConvertTo-Json -InputObject $p -Depth 8) -match '"hotfixes":\s*\[\s*\]') 'hotfixes not []'
}
Test-Case 'Patch: a single hotfix stays an array in JSON' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $today.AddDays(-5)))
    Set-FakeValue 'Read-AgPendingReboot' $false
    Assert-True ((ConvertTo-Json -InputObject (Get-AgPatch) -Depth 8) -match '"hotfixes":\s*\[') 'single not an array'
}
Test-Case 'Patch: 75 days old gives days_since 75' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $today.AddDays(-75)))
    Set-FakeValue 'Read-AgPendingReboot' $false
    Assert-True ((Get-AgPatch)['days_since_latest_hotfix'] -eq 75) 'days'
}
Test-Case 'Patch: th-TH culture still gives Gregorian yyyy-MM-dd' {
    $t = [Threading.Thread]::CurrentThread
    $old = $t.CurrentCulture
    try {
        $t.CurrentCulture = [Globalization.CultureInfo]::GetCultureInfo('th-TH')
        $d = [DateTime]::new(2026, 3, 5, 0, 0, 0, [DateTimeKind]::Utc)
        Set-FakeValue 'Read-AgHotFix' @((New-Hf 'KB5000001' $d))
        Set-FakeValue 'Read-AgPendingReboot' $false
        $p = Get-AgPatch
        Assert-True ($p['latest_hotfix_installed_on'] -ceq '2026-03-05') "latest was $($p['latest_hotfix_installed_on'])"
        Assert-True (@($p['hotfixes'])[0]['installed_on'] -ceq '2026-03-05') 'installed_on'
    } finally { $t.CurrentCulture = $old }
}
Test-Case 'Patch: a reader that throws is failed, error clean' {
    Set-FakeThrow 'Read-AgHotFix'
    Set-FakeValue 'Read-AgPendingReboot' $false
    $p = Get-AgPatch
    Assert-True ($p['status'] -eq 'failed' -and $p['error'] -notmatch 'bob') 'expected clean failed'
}

# =============== Software ===============
function New-App($Name, $Version = '1.0', $Pub = 'Contoso', $Extra = @{}) {
    $o = [ordered]@{ DisplayName = $Name; DisplayVersion = $Version; Publisher = $Pub }
    foreach ($k in $Extra.Keys) { $o[$k] = $Extra[$k] }
    [pscustomobject]$o
}
Test-Case 'Software: healthy, keys and fields' {
    Set-FakeValue 'Read-AgUninstallKeys' @((New-App 'Google Chrome' '130.0' 'Google LLC'))
    $s = Get-AgSoftware
    Assert-True ((Get-Keys $s) -eq 'status,error,installed') "keys: $(Get-Keys $s)"
    $i = @($s['installed'])
    Assert-True ($s['status'] -eq 'ok' -and $i.Count -eq 1 -and $i[0]['name'] -eq 'Google Chrome' -and $i[0]['version'] -eq '130.0' -and $i[0]['publisher'] -eq 'Google LLC') 'fields'
    Assert-True ((Get-Keys $i[0]) -eq 'name,version,publisher') 'item key order'
}
Test-Case 'Software: filter drops blank, SystemComponent, ParentKeyName and updates' {
    Set-FakeValue 'Read-AgUninstallKeys' @(
        (New-App 'Keep Me'), (New-App ''), (New-App $null), (New-App '   '),
        (New-App 'Sys' '1' 'x' @{ SystemComponent = 1 }), (New-App 'Child' '1' 'x' @{ ParentKeyName = 'Parent' }),
        (New-App 'U1' '1' 'x' @{ ReleaseType = 'Update' }), (New-App 'U2' '1' 'x' @{ ReleaseType = 'Hotfix' }), (New-App 'U3' '1' 'x' @{ ReleaseType = 'Security Update' }),
        (New-App 'Sys0' '1' 'x' @{ SystemComponent = 0 }))
    $n = @((Get-AgSoftware)['installed'] | ForEach-Object { $_['name'] }) -join ','
    Assert-True ($n -ceq 'Keep Me,Sys0') "got $n"
}
Test-Case 'Software: trims, missing version and publisher become empty strings' {
    Set-FakeValue 'Read-AgUninstallKeys' @([pscustomobject]@{ DisplayName = '  Tool  ' })
    $i = @((Get-AgSoftware)['installed'])
    Assert-True ($i[0]['name'] -ceq 'Tool' -and $i[0]['version'] -ceq '' -and $i[0]['publisher'] -ceq '') 'expected trimmed/empty strings'
}
Test-Case 'Software: lengths cut to 256 / 64 / 256 (P1)' {
    Set-FakeValue 'Read-AgUninstallKeys' @((New-App ('n' * 300) ('v' * 100) ('p' * 300)))
    $i = @((Get-AgSoftware)['installed'])
    Assert-True ($i[0]['name'].Length -eq 256 -and $i[0]['version'].Length -eq 64 -and $i[0]['publisher'].Length -eq 256) 'lengths'
}
Test-Case 'Software: deduped on name and version, sorted by name' {
    Set-FakeValue 'Read-AgUninstallKeys' @((New-App 'Zed' '1'), (New-App 'Alpha' '2'), (New-App 'Alpha' '2'), (New-App 'Alpha' '1'))
    $n = @((Get-AgSoftware)['installed'] | ForEach-Object { $_['name'] + ' ' + $_['version'] }) -join ','
    Assert-True ($n -ceq 'Alpha 1,Alpha 2,Zed 1') "got $n"
}
Test-Case 'Software: capped at 500' {
    $a = @(); for ($i = 0; $i -lt 600; $i++) { $a += (New-App ('App{0:D4}' -f $i)) }
    Set-FakeValue 'Read-AgUninstallKeys' $a
    Assert-True (@((Get-AgSoftware)['installed']).Count -eq 500) 'cap'
}
Test-Case 'Software: a single entry stays an array in JSON; none is []' {
    Set-FakeValue 'Read-AgUninstallKeys' @((New-App 'One'))
    Assert-True ((ConvertTo-Json -InputObject (Get-AgSoftware) -Depth 8) -match '"installed":\s*\[') 'single not an array'
    Set-FakeValue 'Read-AgUninstallKeys' @()
    $s = Get-AgSoftware
    Assert-True ($s['status'] -eq 'ok' -and (ConvertTo-Json -InputObject $s -Depth 8) -match '"installed":\s*\[\s*\]') 'empty not []'
}
Test-Case 'Software: IOException from the reader is failed with a cleaned error' {
    Set-Fake 'Read-AgUninstallKeys' { throw [System.IO.IOException]::new('simulated registry failure at C:\Users\bob\k') }
    $s = Get-AgSoftware
    Assert-True ($s['status'] -eq 'failed') "status was $($s['status'])"
    Assert-True ($s['error'] -notmatch '[A-Za-z]:\\' -and $s['error'] -notmatch 'bob') "error leaks: $($s['error'])"
    Assert-True (@($s['installed']).Count -eq 0) 'installed should stay empty'
}

# =============== Recovery ===============
$reOn = @('Windows RE status:         Enabled', 'Windows RE location:       \\?\GLOBALROOT\device\x')
function Set-RecoveryFakes {
    Set-FakeValue 'Test-AgAdmin' $true
    Set-FakeValue 'Read-AgReagentc' $reOn
    Set-FakeValue 'Read-AgSystemRestore' ([pscustomobject]@{ RPSessionInterval = 1; DisableSR = 0 })
    Set-FakeValue 'Read-AgRestorePoints' @(
        [pscustomobject]@{ SequenceNumber = 5; CreationTime = '20260301100000.000000+000' },
        [pscustomobject]@{ SequenceNumber = 9; CreationTime = '20260310123000.000000+000' },
        [pscustomobject]@{ SequenceNumber = 7; CreationTime = '20260305090000.000000+000' })
}
Test-Case 'Recovery: healthy admin, keys in schema order, types right' {
    Set-RecoveryFakes
    $r = Get-AgRecovery
    Assert-True ((Get-Keys $r) -eq 'status,error,winre_enabled,system_restore_enabled,restore_point_count,latest_restore_point') "keys: $(Get-Keys $r)"
    Assert-True ($r['status'] -eq 'ok' -and $r['winre_enabled'] -eq $true -and $r['system_restore_enabled'] -eq $true) 'flags'
    Assert-True ($r['restore_point_count'] -is [int] -and $r['restore_point_count'] -eq 3) 'count'
    $exp = ConvertTo-IsoUtc ([Management.ManagementDateTimeConverter]::ToDateTime('20260310123000.000000+000'))
    Assert-True ($r['latest_restore_point'] -ceq $exp) "latest was $($r['latest_restore_point']) expected $exp"
}
Test-Case 'Recovery: WinRE Disabled gives false' {
    Set-RecoveryFakes
    Set-FakeValue 'Read-AgReagentc' @('Windows RE status:         Disabled')
    Assert-True ((Get-AgRecovery)['winre_enabled'] -eq $false) 'expected false'
}
Test-Case 'Recovery: unmatched (localised) reagentc text gives null' {
    Set-RecoveryFakes
    Set-FakeValue 'Read-AgReagentc' @('Estado de Windows RE:  Habilitado')
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $null -eq $r['winre_enabled']) 'expected null/ok'
}
Test-Case 'Recovery: non-admin nulls winre and restore points, readers never called (P3)' {
    Set-RecoveryFakes
    Set-FakeValue 'Test-AgAdmin' $false
    Set-FakeThrow 'Read-AgReagentc'
    Set-FakeThrow 'Read-AgRestorePoints'
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $null -eq $r['winre_enabled'] -and $null -eq $r['restore_point_count'] -and $null -eq $r['latest_restore_point']) "got $($r['status']) $($r['error'])"
    Assert-True ($r['system_restore_enabled'] -eq $true) 'system restore is not admin-only'
}
foreach ($case in @(@(1, 0, $true), @(1, 1, $false), @(0, 0, $false), @(1, $null, $true))) {
    $iv = $case[0]; $dis = $case[1]; $want = $case[2]
    Test-Case "Recovery: RPSessionInterval $iv, DisableSR '$dis' gives $want" {
        Set-RecoveryFakes
        Set-FakeValue 'Read-AgSystemRestore' ([pscustomobject]@{ RPSessionInterval = $iv; DisableSR = $dis })
        Assert-True ((Get-AgRecovery)['system_restore_enabled'] -eq $want) 'wrong'
    }
}
Test-Case 'Recovery: System Restore key missing gives null' {
    Set-RecoveryFakes
    Set-FakeValue 'Read-AgSystemRestore' $null
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $null -eq $r['system_restore_enabled']) 'expected null/ok'
}
Test-Case 'Recovery: no restore points gives count 0 and latest null' {
    Set-RecoveryFakes
    Set-FakeValue 'Read-AgRestorePoints' @()
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $r['restore_point_count'] -eq 0 -and $null -eq $r['latest_restore_point']) 'zero case'
}

# =============== Phase 4 fixes (Socrates round) ===============
function New-ErrRec([string]$Id, [string]$Msg) {
    [Management.Automation.ErrorRecord]::new([InvalidOperationException]::new($Msg), $Id, [Management.Automation.ErrorCategory]::ObjectNotFound, $null)
}
foreach ($id in @('NoMatchingEventsFound,Microsoft.PowerShell.Commands.GetWinEventCommand', 'NoMatchingLogsFound,Microsoft.PowerShell.Commands.GetWinEventCommand')) {
    Test-Case "Backup: error id '$($id.Split(',')[0])' with a non-English message gives null, ok" {
        Set-BackupFakes
        $er = New-ErrRec $id 'Es wurden keine Ereignisse gefunden, die den Auswahlkriterien entsprechen.'
        Set-Fake 'Read-AgBackupEvent' ({ throw $er }.GetNewClosure())
        $b = Get-AgBackup
        Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['windows_backup_last_success']) "got $($b['status']) $($b['error'])"
    }
}
Test-Case 'Backup: unrelated error id is failed even if the text says "not found"' {
    Set-BackupFakes
    $er = New-ErrRec 'SomethingElse,Microsoft.PowerShell.Commands.GetWinEventCommand' 'The thing was not found'
    Set-Fake 'Read-AgBackupEvent' ({ throw $er }.GetNewClosure())
    Assert-True ((Get-AgBackup)['status'] -eq 'failed') 'expected failed'
}
Test-Case 'Backup: FromFileTimeUtc out of range gives null last backup, section ok' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgFileHistory' ([ordered]@{ config_exists = $true; protected_up_to_raw = [long]::MaxValue })
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['file_history_last_backup'] -and $b['file_history_enabled'] -eq $true) "got $($b['status']) $($b['error'])"
    Assert-True ($b['shadow_copy_count'] -eq 3) 'other fields kept'
}
Test-Case 'Backup: byte[] ProtectedUpToTime gives null last backup, section ok' {
    Set-BackupFakes
    Set-FakeValue 'Read-AgFileHistory' ([ordered]@{ config_exists = $true; protected_up_to_raw = [byte[]]@(1, 2, 3) })
    $b = Get-AgBackup
    Assert-True ($b['status'] -eq 'ok' -and $null -eq $b['file_history_last_backup']) "got $($b['status']) $($b['error'])"
}
Test-Case 'Recovery: restore-point reader throws as admin gives null count and latest, rest kept' {
    Set-RecoveryFakes
    Set-FakeThrow 'Read-AgRestorePoints'
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $null -eq $r['restore_point_count'] -and $null -eq $r['latest_restore_point']) "got $($r['status']) $($r['error'])"
    Assert-True ($r['winre_enabled'] -eq $true -and $r['system_restore_enabled'] -eq $true) 'winre and system restore should be kept'
}
Test-Case 'Recovery: reagentc reader throws as admin gives winre null, rest kept' {
    Set-RecoveryFakes
    Set-FakeThrow 'Read-AgReagentc'
    $r = Get-AgRecovery
    Assert-True ($r['status'] -eq 'ok' -and $null -eq $r['winre_enabled']) "got $($r['status']) $($r['error'])"
    Assert-True ($r['restore_point_count'] -eq 3 -and $r['system_restore_enabled'] -eq $true) 'other fields should be kept'
}
Test-Case 'Patch: a hotfix ID with a trailing newline is left out' {
    Set-FakeValue 'Read-AgHotFix' @((New-Hf "KB5000001`n" $today.AddDays(-2)), (New-Hf 'KB5000002' $today.AddDays(-3)))
    Set-FakeValue 'Read-AgPendingReboot' $false
    $kb = @((Get-AgPatch)['hotfixes'] | ForEach-Object { $_['kb'] }) -join ','
    Assert-True ($kb -ceq 'KB5000002') "got '$kb'"
}

# =============== Guard ===============
Test-Case 'Test-ReadOnly.ps1 prints READ-ONLY OK' {
    $out = & powershell.exe -NoProfile -File (Join-Path $PSScriptRoot 'Test-ReadOnly.ps1') 2>&1 | Out-String
    Assert-True ($out -match 'READ-ONLY OK') ('guard output: ' + (($out -split "`r?`n")[0..2] -join ' | '))
}

Write-Output "$script:passed passed, $script:failed failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
