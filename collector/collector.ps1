# collector/collector.ps1  - PowerShell 5.1, READ-ONLY. See manual 3.7.
[CmdletBinding()]
param(
    [string]   $OutputPath,
    [switch]   $DryRun,
    [string[]] $Only,
    [string]   $MockFile,
    [string]   $RunId
)
trap { [Console]::Error.WriteLine('Collector failed'); exit 1 }
$ErrorActionPreference = 'Stop'

# Checked here, not with Validate* attributes, so bad values exit 64 (3.3). -cnotmatch: the schema wants lower-case hex;
# [0-9] not \d (no non-ASCII digits); \z not $ ($ also matches before a trailing newline). run_id names a folder.
if ($PSBoundParameters.Keys -contains 'RunId' -and $RunId -cnotmatch '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}Z_[0-9a-f]{4}\z') {
    [Console]::Error.WriteLine('Bad -RunId'); exit 64
}
foreach ($name in $Only) {
    if (@('Host','Backup','Patch','Software','Protection','Recovery') -notcontains $name) { [Console]::Error.WriteLine('Bad -Only value'); exit 64 }
}
$Version = '0.1.0'
$sw = [Diagnostics.Stopwatch]::StartNew()

. "$PSScriptRoot\lib\Common.ps1"
Get-ChildItem "$PSScriptRoot\probes\*.ps1" | ForEach-Object { . $_.FullName }
if ($MockFile -and -not (Test-Path -LiteralPath $MockFile)) { [Console]::Error.WriteLine('Mock file not found'); exit 64 }
if ($MockFile) { . ([string](Resolve-Path $MockFile)) }   # overrides Get-Ag* functions (3.10)

if (-not $DryRun -and -not $OutputPath) { [Console]::Error.WriteLine('Use -OutputPath <file> or -DryRun'); exit 64 }

$collectedAt = [DateTime]::UtcNow
$scan = [ordered]@{
    schema_version    = '1.0.0'
    run_id            = if ($RunId) { $RunId } else { '{0}_{1}' -f $collectedAt.ToString("yyyy-MM-dd'T'HH-mm-ss'Z'", [Globalization.CultureInfo]::InvariantCulture), (Get-Random -Maximum 65535).ToString('x4') }
    collected_at      = $null          # filled at end
    collector_version = $Version
    duration_ms       = $null
}
$probes = [ordered]@{
    host = { Get-AgHost }; backup = { Get-AgBackup }; patch = { Get-AgPatch }
    software = { Get-AgSoftware }; protection = { Get-AgProtection }; recovery = { Get-AgRecovery }
}
foreach ($key in $probes.Keys) {
    if ($Only -and ($Only -notcontains (Get-Culture).TextInfo.ToTitleCase($key))) { continue }
    if (-not $DryRun) { Write-Output "AG-PHASE:$key" }   # progress marker for the app (4.8); never in -DryRun
    $scan[$key] = & $probes[$key]
}
$scan.collected_at = ConvertTo-IsoUtc ([DateTime]::UtcNow)
$scan.duration_ms  = [int]$sw.ElapsedMilliseconds

Write-ScanJson -Scan $scan -Path $OutputPath -DryRun:$DryRun
exit 0
