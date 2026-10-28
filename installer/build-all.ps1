# installer/build-all.ps1   - run from repo root
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

Write-Host '0/7 Contract check';    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\contract-check.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '1/7 Engine tests';      & "$root\engine\.venv\Scripts\python.exe" -m pytest -q "$root\engine\tests"; if ($LASTEXITCODE) { exit 1 }
Write-Host '2/7 Engine exe';        Push-Location "$root\engine"; & .venv\Scripts\pyinstaller.exe engine.spec --clean --noconfirm; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '3/7 Resource manifest'; Push-Location "$root\desktop"; node ..\installer\make-manifest.mjs; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '4/7 Collector tests';   & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-ReadOnly.ps1"; if ($LASTEXITCODE) { exit 1 }
                                    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-Collector.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '5/7 Desktop install';   Push-Location "$root\desktop"; npm ci --prefer-offline; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '6/7 Desktop tests';     Push-Location "$root\desktop"; npm run typecheck; if ($LASTEXITCODE) { Pop-Location; exit 1 }; npm run test; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '7/7 Installer';         Push-Location "$root\desktop"; npm run dist; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
& "$PSScriptRoot\checksums.ps1"
Write-Host "DONE -> desktop\release" -ForegroundColor Green
