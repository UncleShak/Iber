# collector/mocks/probe-throws.ps1 - 3.10 row "probe-throws" (used from Phase 4)
. "$PSScriptRoot\healthy.ps1"
function Read-AgUninstallKeys { throw [System.IO.IOException]::new('simulated registry failure') }
