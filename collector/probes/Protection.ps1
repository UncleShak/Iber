# collector/probes/Protection.ps1 - protection block (manual 3.5 section 4, 3.6). Readers only.

function ConvertTo-AgBoolOrNull($v) { if ($null -eq $v) { return $null }; return [bool]$v }

function Get-AgDefender {
    Invoke-Probe -Template ([ordered]@{
        antivirus_enabled = $null; realtime_enabled = $null; tamper_protected = $null
        signature_age_days = $null; third_party_av = $null
    }) -Body {
        $third = $null
        foreach ($n in @(Read-AgSecurityCenterAv)) {
            if ("$n" -match '\S' -and "$n" -notmatch 'Windows Defender|Microsoft Defender Antivirus') { $third = "$n"; break }
        }
        try {
            $mp = Read-AgMpStatus
        } catch {
            # a stopped or removed Defender service is a finding, not an error (3.6)
            if ((Read-AgServiceStatus 'WinDefend') -eq 'Running') { throw }
            return @{ antivirus_enabled = $false; realtime_enabled = $false; third_party_av = $third }
        }
        $age = $null
        if ($null -ne $mp.AntivirusSignatureAge -and $mp.AntivirusSignatureAge -le 2147483647) { $age = [int]$mp.AntivirusSignatureAge }   # uint32 max means never updated
        return @{
            antivirus_enabled  = ConvertTo-AgBoolOrNull $mp.AntivirusEnabled
            realtime_enabled   = ConvertTo-AgBoolOrNull $mp.RealTimeProtectionEnabled
            tamper_protected   = ConvertTo-AgBoolOrNull $mp.IsTamperProtected
            signature_age_days = $age
            third_party_av     = $third
        }
    }
}

# Get-MpPreference through the reader; $null when it cannot be read (the registry fallback then applies).
function Get-AgPreferenceOrNull {
    try { return (Read-AgMpPreference) } catch { return $null }
}

function Get-AgCfa {
    Invoke-Probe -Template ([ordered]@{ mode = $null }) -Body {
        $code = $null
        $pref = Get-AgPreferenceOrNull
        if ($null -ne $pref) { $code = $pref.EnableControlledFolderAccess }
        if ($null -eq $code) { $code = Read-AgCfaRegistry }
        $mode = $null
        if ($null -ne $code) {
            switch ([int]$code) {
                0 { $mode = 'disabled' }
                1 { $mode = 'enabled' }
                2 { $mode = 'audit' }
                3 { $mode = 'enabled' }
                4 { $mode = 'audit' }
            }
        }
        return @{ mode = $mode }
    }
}

function ConvertTo-AgAsrAction($code) {
    switch ([int]$code) {
        0 { return 'off' }
        1 { return 'block' }
        2 { return 'audit' }
        5 { return 'off' }
        6 { return 'warn' }
    }
    return $null
}

function Get-AgAsr {
    Invoke-Probe -Template ([ordered]@{ rules = @() }) -Body {
        $pairs = [ordered]@{}
        $pref = Get-AgPreferenceOrNull
        if ($null -ne $pref) {
            $ids = @($pref.AttackSurfaceReductionRules_Ids | Where-Object { $null -ne $_ })
            $acts = @($pref.AttackSurfaceReductionRules_Actions | Where-Object { $null -ne $_ })
            for ($i = 0; $i -lt $ids.Count -and $i -lt $acts.Count; $i++) { $pairs["$($ids[$i])"] = $acts[$i] }
        }
        if ($pairs.Count -eq 0) {
            $reg = Read-AgAsrRegistry
            foreach ($k in @($reg.Keys)) { $pairs["$k"] = $reg[$k] }
        }
        $rules = @()
        foreach ($id in @($pairs.Keys)) {
            if ($id -notmatch '^[0-9a-fA-F-]{36}$') { continue }
            $action = ConvertTo-AgAsrAction $pairs[$id]
            if ($null -ne $action) { $rules += [ordered]@{ id = $id; action = $action } }
        }
        return @{ rules = $rules }
    }
}

function ConvertTo-AgBitLockerCom($code) {
    if ($null -eq $code) { return $null }
    switch ([int]$code) {
        1 { return 'on' }
        2 { return 'off' }
        3 { return 'off' }   # encrypting counts as not yet protected
    }
    return $null
}

function Get-AgBitLocker {
    Invoke-Probe -Template ([ordered]@{
        os_volume_protection = $null; os_volume_encryption_pct = $null; encryption_method = $null
    }) -Body {
        if (([string](Read-AgEdition)) -like 'Core*') {
            throw [AgUnavailable]::new('BitLocker management not available on Windows Home')
        }
        $admin = [bool](Test-AgAdmin)
        if ($admin -and (Read-AgHasBitLockerCmdlet)) {
            $v = Read-AgBitLocker
            $prot = $null
            switch ([string]$v.ProtectionStatus) {
                'On'  { $prot = 'on' }
                'Off' { $prot = 'off' }
            }
            $pct = $null
            if ($null -ne $v.EncryptionPercentage) { $e = $v.EncryptionPercentage; $pct = [int]($e - ($e % 1)) }   # truncate, never round up
            $method = $null
            if ($null -ne $v.EncryptionMethod) { $method = [string]$v.EncryptionMethod }
            return @{ os_volume_protection = $prot; os_volume_encryption_pct = $pct; encryption_method = $method }
        }
        $prot = ConvertTo-AgBitLockerCom (Read-AgBitLockerCom)
        if ($null -eq $prot) {
            if (-not $admin) { throw [AgUnavailable]::new('Requires administrator rights') }
            throw [AgUnavailable]::new('BitLocker status not readable on this PC')
        }
        return @{ os_volume_protection = $prot }
    }
}

function Get-AgProtection {
    [ordered]@{
        bitlocker = Get-AgBitLocker
        defender  = Get-AgDefender
        cfa       = Get-AgCfa
        asr       = Get-AgAsr
    }
}
