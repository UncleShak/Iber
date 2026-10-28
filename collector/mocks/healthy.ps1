# collector/mocks/healthy.ps1 - base for the 3.10 mocks: fixed healthy values for every reader the Host and Protection probes use.
# Case mocks dot-source this first, so a mock run never reads the real PC.
function Read-AgComputerName { 'MOCK-PC' }
function Read-AgOsCaption { 'Microsoft Windows 11 Pro' }
function Read-AgOsBuild { '22631' }
function Read-AgEdition { 'Professional' }
function Read-AgPsVersion { '5.1.22621.4391' }
function Test-AgAdmin { $true }
function Read-AgMpStatus {
    [pscustomobject]@{ AntivirusEnabled = $true; RealTimeProtectionEnabled = $true; IsTamperProtected = $true
        AntivirusSignatureAge = 1; AMRunningMode = 'Normal' }
}
function Read-AgServiceStatus([string]$Name) { 'Running' }
function Read-AgSecurityCenterAv { @('Windows Defender') }
function Read-AgMpPreference {
    [pscustomobject]@{ EnableControlledFolderAccess = 1
        AttackSurfaceReductionRules_Ids = @('d4f940ab-401b-4efc-aadc-ad5f3c50688a')
        AttackSurfaceReductionRules_Actions = @(1) }
}
function Read-AgCfaRegistry { 1 }
function Read-AgAsrRegistry { [ordered]@{ 'd4f940ab-401b-4efc-aadc-ad5f3c50688a' = 1 } }
function Read-AgHasBitLockerCmdlet { $true }
function Read-AgBitLocker { [pscustomobject]@{ ProtectionStatus = 'On'; EncryptionPercentage = 100; EncryptionMethod = 'XtsAes128' } }
function Read-AgBitLockerCom { 1 }
