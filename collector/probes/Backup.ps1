# collector/probes/Backup.ps1 - backup block (manual 3.5 item 1). Readers only; admin-only fields come from Test-AgAdmin (P3).
function Get-AgBackup {
    Invoke-Probe -Template ([ordered]@{
        file_history_enabled = $null; file_history_last_backup = $null; windows_backup_last_success = $null
        onedrive_kfm_folders = @(); shadow_copy_count = $null; third_party_agents = @()
    }) -Body {
        $admin = [bool](Test-AgAdmin)
        $services = @(Read-AgServices)

        $fh = Read-AgFileHistory
        $svcStart = $null
        foreach ($s in $services) { if ($s.Name -ieq 'fhsvc') { $svcStart = [string]$s.StartType; break } }
        $fhEnabled = [bool]$fh['config_exists'] -and ($svcStart -ne 'Disabled')
        $fhLast = $null
        $raw = $fh['protected_up_to_raw']
        if ([bool]$fh['config_exists'] -and $null -ne $raw -and $raw -ne 0) {
            # a bad value (wrong type, out of range) only blanks this field
            try { $fhLast = ConvertTo-IsoUtc ([DateTime]::FromFileTimeUtc($raw)) } catch { $fhLast = $null }
        }

        $winBackup = $null
        $shadow = $null
        if ($admin) {
            try {
                $ev = @(Read-AgBackupEvent)
                if ($ev.Count -gt 0 -and $null -ne $ev[0]) { $winBackup = ConvertTo-IsoUtc ([DateTime]$ev[0].TimeCreated) }
            } catch {
                if ($_.FullyQualifiedErrorId -notlike 'NoMatchingEventsFound,*' -and $_.FullyQualifiedErrorId -notlike 'NoMatchingLogsFound,*') { throw }
            }
            $shadow = @(Read-AgShadowCopies).Count
        }

        $folders = Read-AgShellFolders
        $kfm = @()
        if ("$($folders['Desktop'])" -like '*\OneDrive*') { $kfm += 'Desktop' }
        if ("$($folders['Personal'])" -like '*\OneDrive*') { $kfm += 'Documents' }
        if ("$($folders['My Pictures'])" -like '*\OneDrive*') { $kfm += 'Pictures' }

        $vendors = [ordered]@{
            'Veeam*' = 'Veeam'; 'Acronis*' = 'Acronis'; 'Macrium*' = 'Macrium'; 'Backblaze*' = 'Backblaze'; 'Carbonite*' = 'Carbonite'
            'Datto*' = 'Datto'; '*Synology*Active Backup*' = 'Synology Active Backup'; 'CrashPlan*' = 'CrashPlan'; 'IDrive*' = 'IDrive'
        }
        $agents = @()
        foreach ($pattern in @($vendors.Keys)) {
            foreach ($s in $services) {
                if ("$($s.Name)" -like $pattern -or "$($s.DisplayName)" -like $pattern) { $agents += $vendors[$pattern]; break }
            }
        }

        return @{
            file_history_enabled = $fhEnabled; file_history_last_backup = $fhLast; windows_backup_last_success = $winBackup
            onedrive_kfm_folders = $kfm; shadow_copy_count = $shadow; third_party_agents = $agents
        }
    }
}
