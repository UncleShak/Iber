# installer/stubs/collector-stub.ps1
# Stub collector for Brick D isolation testing (AG_STUB=1).
# Prints AG-PHASE markers and copies scan.stub.json to -OutputPath.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[0-9a-f]{4}$')]
    [string]$RunId
)

$ErrorActionPreference = 'Stop'

Write-Output "AG-PHASE:host"
Start-Sleep -Milliseconds 200

Write-Output "AG-PHASE:backup"
Start-Sleep -Milliseconds 300

Write-Output "AG-PHASE:patch"
Start-Sleep -Milliseconds 200

Write-Output "AG-PHASE:software"
Start-Sleep -Milliseconds 200

Write-Output "AG-PHASE:protection"
Start-Sleep -Milliseconds 300

Write-Output "AG-PHASE:recovery"
Start-Sleep -Milliseconds 200

# Copy the stub fixture to the output path
$stubPath = Join-Path $PSScriptRoot "scan.stub.json"
if (-not (Test-Path $stubPath)) {
    Write-Error "Stub fixture not found: $stubPath"
    exit 1
}

Copy-Item -Path $stubPath -Destination $OutputPath -Force
exit 0
