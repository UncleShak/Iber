# collector/probes/Patch.ps1 - patch block (manual 3.5 item 2). IDs not matching ^KB\d+$ are listed nowhere but still counted (P2).
function Get-AgPatch {
    Invoke-Probe -Template ([ordered]@{
        hotfix_count = $null; latest_hotfix_installed_on = $null; days_since_latest_hotfix = $null; hotfixes = @(); pending_reboot = $null
    }) -Body {
        $all = @(Read-AgHotFix)
        $dated = @($all | Where-Object { $null -ne $_.InstalledOn } | Sort-Object -Property InstalledOn -Descending)
        if ($all.Count -gt 0 -and $dated.Count -eq 0) { throw [AgUnavailable]::new('Update dates unreadable on this PC') }
        $list = @()
        foreach ($h in $dated) {
            if ($list.Count -ge 10) { break }
            if ("$($h.HotFixID)" -cmatch '^KB[0-9]+\z') {
                $list += [ordered]@{ kb = [string]$h.HotFixID; installed_on = $h.InstalledOn.ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture) }
            }
        }
        $latest = $null
        $days = $null
        if ($dated.Count -gt 0) {
            $latest = $dated[0].InstalledOn.ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
            $days = [int]([DateTime]::UtcNow.Date - $dated[0].InstalledOn.Date).TotalDays
        }
        return @{
            hotfix_count = $all.Count; latest_hotfix_installed_on = $latest; days_since_latest_hotfix = $days
            hotfixes = $list; pending_reboot = [bool](Read-AgPendingReboot)
        }
    }
}
