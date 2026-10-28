# collector/probes/Software.ps1 - software block (manual 3.5 item 3). Lengths cut to the schema limits (P1).
function ConvertTo-AgCut($v, [int]$Max) {
    $t = ("$v" -replace '^\s+|\s+$', '')
    if ($t.Length -gt $Max) { $t = $t.Substring(0, $Max) -replace '\s+$', '' }
    return $t
}
function Get-AgSoftware {
    Invoke-Probe -Template ([ordered]@{ installed = @() }) -Body {
        $items = @()
        foreach ($k in @(Read-AgUninstallKeys)) {
            if ($null -eq $k -or "$($k.DisplayName)" -notmatch '\S') { continue }
            if ($k.SystemComponent -eq 1 -or $k.ParentKeyName) { continue }
            if (@('Update', 'Hotfix', 'Security Update') -contains "$($k.ReleaseType)") { continue }
            $name = ConvertTo-AgCut $k.DisplayName 256
            if ($name.Length -eq 0) { continue }
            $items += [ordered]@{ name = $name; version = (ConvertTo-AgCut $k.DisplayVersion 64); publisher = (ConvertTo-AgCut $k.Publisher 256) }
        }
        $installed = @()
        foreach ($i in @($items | Sort-Object -Property @{ Expression = { $_['name'] } }, @{ Expression = { $_['version'] } } -Unique)) {
            if ($installed.Count -ge 500) { break }
            $installed += [ordered]@{ name = $i['name']; version = $i['version']; publisher = $i['publisher'] }
        }
        return @{ installed = $installed }
    }
}
