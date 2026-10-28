# installer/checksums.ps1
$exe = Get-ChildItem (Join-Path $PSScriptRoot '..\desktop\release\Antigravity-Setup-*.exe') | Select-Object -First 1
$hash = (Get-FileHash $exe.FullName -Algorithm SHA256).Hash
"$hash  $($exe.Name)" | Set-Content (Join-Path $exe.DirectoryName 'SHA256SUMS.txt') -Encoding ascii
Write-Host $hash
