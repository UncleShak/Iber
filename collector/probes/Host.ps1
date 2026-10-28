# collector/probes/Host.ps1 - host block (manual 3.5 Host). Not wrapped in Invoke-Probe: a failed read stops the collector.
function Get-AgHost {
    [ordered]@{
        hostname_hash = Get-AgHash ([string](Read-AgComputerName))
        os_caption    = [string](Read-AgOsCaption)
        os_build      = Get-AgOsBuildChecked
        os_edition    = [string](Read-AgEdition)
        is_admin      = [bool](Test-AgAdmin)
        ps_version    = [string](Read-AgPsVersion)
    }
}

function Get-AgOsBuildChecked {
    $b = [string](Read-AgOsBuild)
    if ($b -notmatch '^\d+$') { throw 'OS build unreadable' }
    return $b
}
