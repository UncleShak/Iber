# collector/lib/Common.ps1 - shared helpers and raw readers (manual 3.4, 3.8, 3.10). READ-ONLY.

$AgHostSalt = 'antigravity-host-v1'

class AgUnavailable : System.Exception { AgUnavailable([string]$m) : base($m) {} }

function ConvertTo-AgSafeError([string]$Text) {
    if ($null -eq $Text) { return $null }
    $t = $Text
    # paths: from the start marker up to the next quote or end of string (over-scrubbing is fine, leaking is not)
    $t = [regex]::Replace($t, '(?:\\|file:|[A-Za-z]:[\/])[^''"`]*', '<path>', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $t = [regex]::Replace($t, 'S-1-\d+(?:-\d+)+', '<sid>')
    $names = @($env:USERNAME, $env:COMPUTERNAME)
    if (-not [string]::IsNullOrEmpty($env:USERPROFILE)) { $names += [IO.Path]::GetFileName($env:USERPROFILE.TrimEnd('\', '/')) }
    foreach ($v in $names) {
        if (-not [string]::IsNullOrEmpty($v)) {
            $pat = '(?<![A-Za-z0-9])' + [regex]::Escape($v) + '(?![A-Za-z0-9])'
            $t = [regex]::Replace($t, $pat, '<redacted>', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
        }
    }
    if ($t.Length -gt 200) { $t = $t.Substring(0, 200) }
    return $t
}

function Invoke-Probe {
    param([scriptblock]$Body, [System.Collections.Specialized.OrderedDictionary]$Template)
    $result = [ordered]@{ status = 'ok'; error = $null }
    foreach ($k in $Template.Keys) { $result[$k] = $Template[$k] }
    try {
        $data = & $Body
        foreach ($k in $data.Keys) { $result[$k] = $data[$k] }
    } catch [AgUnavailable] {
        $result.status = 'unavailable'
        $result.error  = ConvertTo-AgSafeError $_.Exception.Message
    } catch {
        $result.status = 'failed'
        $result.error  = ConvertTo-AgSafeError ($_.CategoryInfo.Reason + ': ' + $_.Exception.Message)
    }
    return $result
}

function Test-AgAdmin {
    [bool]([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function ConvertTo-IsoUtc($d) {
    if ($null -eq $d) { return $null }
    if (-not ($d -is [DateTime])) { throw [ArgumentException]::new('ConvertTo-IsoUtc needs a DateTime') }
    $d.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", [Globalization.CultureInfo]::InvariantCulture)
}

function Get-AgHash([string]$Name) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($AgHostSalt + $Name))
    } finally { $sha.Dispose() }
    'sha256:' + (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Write-ScanJson($Scan, [string]$Path, [switch]$DryRun) {
    $json = ConvertTo-Json -InputObject $Scan -Depth 8
    if ($DryRun) { Write-Output $json; return }
    try {
        $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
        [IO.File]::WriteAllText($full, $json, (New-Object Text.UTF8Encoding $false))
    } catch {
        [Console]::Error.WriteLine('Cannot write output')
        exit 70
    }
}

# ---- Readers: thin, raw, no decisions. Mocks override these (3.10). ----
$AgNtCv = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$AgCfaPolicy = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access'
$AgCfaLocal  = 'HKLM:\SOFTWARE\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access'
$AgAsrPolicy = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Windows Defender Exploit Guard\ASR\Rules'

function Read-AgOsCaption { (Get-CimInstance -ClassName Win32_OperatingSystem).Caption }
function Read-AgOsBuild { (Get-ItemProperty $AgNtCv).CurrentBuild }
function Read-AgEdition { (Get-ItemProperty $AgNtCv).EditionID }
function Read-AgMpStatus { Get-MpComputerStatus }
function Read-AgMpPreference { Get-MpPreference }
function Read-AgServiceStatus([string]$Name) {
    $s = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $s) { return $null }
    [string]$s.Status
}
function Read-AgServices { @(Get-Service -ErrorAction SilentlyContinue | Select-Object Name, DisplayName, Status, StartType) }
function Read-AgSecurityCenterAv {
    @(Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue |
        ForEach-Object { $_.displayName })
}
function Read-AgBitLocker { Get-BitLockerVolume -MountPoint $env:SystemDrive }
function Read-AgBitLockerCom {
    (New-Object -ComObject Shell.Application).NameSpace("$env:SystemDrive\").Self.ExtendedProperty('System.Volume.BitLockerProtection')
}
function Read-AgCfaRegistry {
    foreach ($k in @($AgCfaPolicy, $AgCfaLocal)) {
        $p = Get-ItemProperty -Path $k -Name EnableControlledFolderAccess -ErrorAction SilentlyContinue
        if ($null -ne $p -and $null -ne $p.EnableControlledFolderAccess) { return $p.EnableControlledFolderAccess }
    }
    return $null
}
function Read-AgAsrRegistry {
    $r = [ordered]@{}
    $p = Get-ItemProperty -Path $AgAsrPolicy -ErrorAction SilentlyContinue
    if ($null -ne $p) {
        foreach ($prop in $p.PSObject.Properties) {
            if ($prop.Name -like 'PS*') { continue }
            $r[$prop.Name] = [int]$prop.Value
        }
    }
    return $r
}
function Read-AgHotFix { @(Get-HotFix) }
function Read-AgPendingReboot {
    [bool]((Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') -or
           (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'))
}
function Read-AgUninstallKeys {
    $roots = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
               'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
               'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')
    @(foreach ($r in $roots) { Get-ItemProperty -Path $r -ErrorAction SilentlyContinue })
}
function Read-AgFileHistory {
    $fh = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\FileHistory' -ErrorAction SilentlyContinue
    [ordered]@{
        config_exists       = Test-Path "$env:LOCALAPPDATA\Microsoft\Windows\FileHistory\Configuration\Config1.xml"
        protected_up_to_raw = if ($null -ne $fh) { $fh.ProtectedUpToTime } else { $null }
    }
}
function Read-AgShellFolders {
    $sf = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    [ordered]@{ Desktop = $sf.Desktop; Personal = $sf.Personal; 'My Pictures' = $sf.'My Pictures' }
}
function Read-AgBackupEvent { Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Backup'; Id = 4 } -MaxEvents 1 }
function Read-AgShadowCopies { @(Get-CimInstance -ClassName Win32_ShadowCopy) }
function Read-AgReagentc {
    $ErrorActionPreference = 'Continue'
    & "$env:SystemRoot\System32\reagentc.exe" /info 2>&1 | ForEach-Object { "$_" }
}
function Read-AgSystemRestore {
    Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore' -ErrorAction SilentlyContinue
}
function Read-AgRestorePoints { @(Get-ComputerRestorePoint) }
function Read-AgPsVersion { $PSVersionTable.PSVersion.ToString() }
function Read-AgComputerName { $env:COMPUTERNAME }
function Read-AgHasBitLockerCmdlet { $null -ne (Get-Command Get-BitLockerVolume -ErrorAction SilentlyContinue) }
