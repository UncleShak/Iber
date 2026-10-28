# collector/mocks/stale-patches.ps1 - 3.10 row "stale-patches" (used from Phase 4)
. "$PSScriptRoot\healthy.ps1"
function Read-AgHotFix { @([pscustomobject]@{ HotFixID = 'KB5000001'; InstalledOn = [DateTime]::UtcNow.AddDays(-75) }) }
