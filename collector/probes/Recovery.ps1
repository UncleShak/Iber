# collector/probes/Recovery.ps1 - recovery block (manual 3.5 item 5). WinRE and restore points are admin-only (P3).
function Get-AgRecovery {
    Invoke-Probe -Template ([ordered]@{
        winre_enabled = $null; system_restore_enabled = $null; restore_point_count = $null; latest_restore_point = $null
    }) -Body {
        $admin = [bool](Test-AgAdmin)
        $winre = $null
        $count = $null
        $latest = $null
        if ($admin) {
            # each read below may fail on its own (e.g. reagentc.exe missing); a failure only blanks its own fields
            try {
                $text = (@(Read-AgReagentc) -join "`n")
                if ($text -match 'Windows RE status:\s+Enabled') { $winre = $true }
                elseif ($text -match 'Windows RE status:\s+Disabled') { $winre = $false }
            } catch { $winre = $null }
            try {
                $rp = @(Read-AgRestorePoints)
                $n = $rp.Count
                $when = $null
                if ($rp.Count -gt 0) {
                    $last = @($rp | Sort-Object -Property SequenceNumber)[-1]
                    $when = ConvertTo-IsoUtc ([Management.ManagementDateTimeConverter]::ToDateTime([string]$last.CreationTime))
                }
                $count = $n
                $latest = $when
            } catch { $count = $null; $latest = $null }
        }
        $sr = Read-AgSystemRestore
        $srOn = $null
        if ($null -ne $sr) { $srOn = ($sr.RPSessionInterval -eq 1 -and $sr.DisableSR -ne 1) }
        return @{ winre_enabled = $winre; system_restore_enabled = $srOn; restore_point_count = $count; latest_restore_point = $latest }
    }
}
