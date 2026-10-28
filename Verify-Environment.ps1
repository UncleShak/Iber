# Verify-Environment.ps1
# Run from the root of the antigravity repository
$ErrorActionPreference = 'Continue'
Write-Host "=== ANTIGRAVITY: SHAKIR'S PRE-FLIGHT CHECK ===" -ForegroundColor Cyan

# 1. Toolchain & Version Matrix[cite: 1]
Write-Host "`n[1/4] Checking Toolchain Versions..." -ForegroundColor Yellow
$tools = @(
    @{ Name = "Node.js (Expected v22.x)"; Cmd = "node -v" }
    @{ Name = "npm (Expected 10.9.x)"; Cmd = "npm -v" }
    @{ Name = "Python (Expected 3.12.8)"; Cmd = "py -3.12 --version" }
    @{ Name = "pip (Expected 24.3.1)"; Cmd = "py -3.12 -m pip --version" }
    @{ Name = "Git"; Cmd = "git --version" }
)

foreach ($tool in $tools) {
    try {
        $result = Invoke-Expression $tool.Cmd 2>&1
        Write-Host "  [OK] $($tool.Name): $result" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $($tool.Name) not found or errored." -ForegroundColor Red
    }
}

Write-Host "  [OK] PowerShell Version: $($PSVersionTable.PSVersion.ToString())" -ForegroundColor Green

# 2. Offline Caches & Wheelhouse[cite: 1]
Write-Host "`n[2/4] Checking Offline Caches..." -ForegroundColor Yellow
$caches = @(
    @{ Name = "Electron Binary Cache"; Path = "$env:LOCALAPPDATA\electron\Cache\*\electron-v34.0.0-win32-x64.zip" }
    @{ Name = "Python Wheelhouse"; Path = ".\.offline\wheelhouse" }
    @{ Name = "Offline Tools (Sysinternals)"; Path = ".\.offline\tools\Procmon64.exe" }
)

foreach ($cache in $caches) {
    if (Test-Path $cache.Path) {
        Write-Host "  [OK] Found $($cache.Name)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Missing $($cache.Name) at $($cache.Path)" -ForegroundColor Red
    }
}

# 3. Brick B: Collector Isolation Tests[cite: 1]
Write-Host "`n[3/4] Running Brick B Isolation Tests..." -ForegroundColor Yellow
if (Test-Path ".\collector\tests\Test-ReadOnly.ps1") {
    Write-Host "  Running Test-ReadOnly.ps1..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\collector\tests\Test-ReadOnly.ps1"
    if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Read-Only Constraints Passed" -ForegroundColor Green } 
    else { Write-Host "  [FAIL] Read-Only Constraints Failed" -ForegroundColor Red }

    Write-Host "  Running Test-Collector.ps1..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\collector\tests\Test-Collector.ps1"
    if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Collector Mock Tests Passed" -ForegroundColor Green } 
    else { Write-Host "  [FAIL] Collector Mock Tests Failed" -ForegroundColor Red }
} else {
    Write-Host "  [WARN] Collector test files not found. Are you in the repo root?" -ForegroundColor DarkYellow
}

# 4. License Generation Artefacts[cite: 1]
Write-Host "`n[4/4] Checking License Keys..." -ForegroundColor Yellow
if (Test-Path "$env:USERPROFILE\.antigravity-private.pem") {
    Write-Host "  [OK] Private key secured in user profile." -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Private key missing from $env:USERPROFILE" -ForegroundColor Red
}

if (Test-Path ".\shared\license\public-key.pem") {
    Write-Host "  [OK] Public key present in shared/license." -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Public key missing." -ForegroundColor Red
}

Write-Host "`n=== VERIFICATION COMPLETE ===" -ForegroundColor Cyan