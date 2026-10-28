# collector/mocks/defender-off.ps1 - 3.10 row "defender-off"
. "$PSScriptRoot\healthy.ps1"
function Read-AgMpStatus { throw 'Service not running' }
function Read-AgServiceStatus([string]$Name) { if ($Name -eq 'WinDefend') { 'Stopped' } else { 'Running' } }
