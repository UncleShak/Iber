# Mock: proves a Read-Ag* override reaches the output (manual 3.10)
. "$PSScriptRoot\stub-probes.ps1"
function Read-AgEdition { 'MockCore' }
function Get-AgHost {
    [ordered]@{
        hostname_hash = 'sha256:0000000000000000000000000000000000000000000000000000000000000000'
        os_caption    = 'Microsoft Windows 11 Pro'
        os_build      = '22631'
        os_edition    = Read-AgEdition
        is_admin      = $true
        ps_version    = '5.1.22621.4391'
    }
}
