# installer/smoke-test.ps1 - automates clean-VM install/uninstall checks (manual 5.9, steps 6, 17, 20)
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('AfterInstall', 'AfterUninstall')]
    [string]$Phase = 'AfterInstall'
)

$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\Antigravity'
$appDataDir = Join-Path $env:APPDATA 'Antigravity'
$localDataDir = Join-Path $env:LOCALAPPDATA 'Antigravity'
$desktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Antigravity.lnk'
$startMenuShortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'Antigravity.lnk'

$failures = @()
function Assert-Check([bool]$Condition, [string]$Desc) {
    if ($Condition) {
        Write-Host "PASS: $Desc" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $Desc" -ForegroundColor Red
        $script:failures += $Desc
    }
}

if ($Phase -eq 'AfterInstall') {
    Assert-Check (Test-Path (Join-Path $installDir 'Antigravity.exe')) 'Antigravity.exe installed in %LOCALAPPDATA%\Programs\Antigravity'
    Assert-Check (Test-Path (Join-Path $installDir 'resources\engine\engine.exe')) 'resources\engine\engine.exe exists'
    Assert-Check (Test-Path (Join-Path $installDir 'resources\engine\_internal')) 'resources\engine\_internal exists'
    Assert-Check (Test-Path (Join-Path $installDir 'resources\collector\collector.ps1')) 'resources\collector\collector.ps1 exists'
    Assert-Check (Test-Path (Join-Path $installDir 'resources\baseline\software-baseline.json')) 'resources\baseline\software-baseline.json exists'
    Assert-Check (-not (Test-Path (Join-Path $installDir 'resources\collector\tests'))) 'collector\tests not shipped'
    Assert-Check (-not (Test-Path (Join-Path $installDir 'resources\collector\mocks'))) 'collector\mocks not shipped'
    Assert-Check (Test-Path $desktopShortcut) 'Desktop shortcut exists'
    Assert-Check (Test-Path $startMenuShortcut) 'Start Menu shortcut exists'

    $runsDir = Join-Path $localDataDir 'runs'
    if (Test-Path $runsDir) {
        $runCount = @(Get-ChildItem $runsDir -Directory).Count
        Assert-Check ($runCount -le 1) "Runs folder keeps at most 1 run (found $runCount)"
    }
} else {
    Assert-Check (-not (Test-Path $installDir)) '%LOCALAPPDATA%\Programs\Antigravity removed'
    Assert-Check (-not (Test-Path $appDataDir)) '%APPDATA%\Antigravity removed'
    Assert-Check (-not (Test-Path $localDataDir)) '%LOCALAPPDATA%\Antigravity removed'
    Assert-Check (-not (Test-Path $desktopShortcut)) 'Desktop shortcut removed'
    Assert-Check (-not (Test-Path $startMenuShortcut)) 'Start Menu shortcut removed'
}

if ($failures.Count -gt 0) {
    Write-Host "SMOKE TEST FAILED ($($failures.Count) failed)" -ForegroundColor Red
    exit 1
}
Write-Host "SMOKE TEST OK ($Phase)" -ForegroundColor Green
exit 0
