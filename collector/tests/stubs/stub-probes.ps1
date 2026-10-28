# Stub probes for skeleton tests (section 0.5 shapes, fixed values, no personal data)

function Get-AgHost {
    [ordered]@{
        hostname_hash = 'sha256:0000000000000000000000000000000000000000000000000000000000000000'
        os_caption    = 'Microsoft Windows 11 Pro'
        os_build      = '22631'
        os_edition    = 'Professional'
        is_admin      = $true
        ps_version    = '5.1.22621.4391'
    }
}

function Get-AgBackup {
    [ordered]@{
        status                      = 'ok'
        error                       = $null
        file_history_enabled        = $true
        file_history_last_backup    = '2026-11-13T22:00:00Z'
        windows_backup_last_success = $null
        onedrive_kfm_folders        = @('Desktop', 'Documents')
        shadow_copy_count           = 3
        third_party_agents          = @('Veeam Agent')
    }
}

function Get-AgPatch {
    [ordered]@{
        status                     = 'ok'
        error                      = $null
        hotfix_count               = 1
        latest_hotfix_installed_on = '2026-11-05'
        days_since_latest_hotfix   = 9
        hotfixes                   = @( [ordered]@{ kb = 'KB5044285'; installed_on = '2026-11-05' } )
        pending_reboot             = $false
    }
}

function Get-AgSoftware {
    [ordered]@{
        status    = 'ok'
        error     = $null
        installed = @( [ordered]@{ name = 'Google Chrome'; version = '130.0.6723.117'; publisher = 'Google LLC' } )
    }
}

function Get-AgProtection {
    [ordered]@{
        bitlocker = [ordered]@{
            status                    = 'ok'
            error                     = $null
            os_volume_protection      = 'on'
            os_volume_encryption_pct  = 100
            encryption_method         = 'XtsAes128'
        }
        defender  = [ordered]@{
            status             = 'ok'
            error              = $null
            antivirus_enabled  = $true
            realtime_enabled   = $true
            tamper_protected   = $true
            signature_age_days = 0
            third_party_av     = $null
        }
        cfa       = [ordered]@{
            status = 'ok'
            error  = $null
            mode   = 'enabled'
        }
        asr       = [ordered]@{
            status = 'ok'
            error  = $null
            rules  = @( [ordered]@{ id = 'd4f940ab-401b-4efc-aadc-ad5f3c50688a'; action = 'block' } )
        }
    }
}

function Get-AgRecovery {
    [ordered]@{
        status                = 'ok'
        error                 = $null
        winre_enabled         = $true
        system_restore_enabled = $true
        restore_point_count   = 2
        latest_restore_point  = '2026-11-10T09:12:00Z'
    }
}
