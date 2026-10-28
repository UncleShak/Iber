# collector/mocks/non-admin.ps1 - 3.10 row "non-admin"
. "$PSScriptRoot\healthy.ps1"
function Test-AgAdmin { $false }
