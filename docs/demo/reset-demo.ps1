# docs/demo/reset-demo.ps1
Remove-Item "$env:APPDATA\Antigravity\desktop-app\license.txt" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Antigravity\license.txt" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Antigravity\runs\*" -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path "$PSScriptRoot\demo-key.txt") {
    Get-Content "$PSScriptRoot\demo-key.txt" -Raw | Set-Clipboard
}

Write-Host "Reset done. Now open Antigravity to start at the License screen." -ForegroundColor Green
