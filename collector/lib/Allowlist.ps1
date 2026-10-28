# collector/lib/Allowlist.ps1 - commands the collector may use (manual 3.7). Adding to it requires Tshedi's review.
$AgAllowedCommands = @(
    'Get-CimInstance', 'Get-ItemProperty', 'Get-ChildItem', 'Get-Service', 'Get-HotFix',
    'Get-MpComputerStatus', 'Get-MpPreference', 'Get-BitLockerVolume', 'Get-ComputerRestorePoint', 'Get-WinEvent',
    'Get-Command', 'Get-Random', 'Get-Culture', 'Test-Path', 'Where-Object', 'ForEach-Object', 'Sort-Object',
    'Select-Object', 'Resolve-Path', 'ConvertTo-Json', 'Write-Error', 'Write-Output',
    'New-Object',   # COM read fallback only - reviewed by hand
    'reagentc.exe'
)
