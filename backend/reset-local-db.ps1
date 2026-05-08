# Reset SQLite DB so OAuth tokens match your current MASTER_ENCRYPTION_KEY.
# REQUIRED: Stop the API first (Ctrl+C in the terminal running uvicorn), then run:
#   .\reset-local-db.ps1

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$db = Join-Path $here "draftly.db"

if (-not (Test-Path $db)) {
    Write-Host "No draftly.db found - nothing to reset."
    exit 0
}

try {
    $bak = Join-Path $here ("draftly.db.bak-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
    Copy-Item -LiteralPath $db -Destination $bak -Force
    Remove-Item -LiteralPath $db -Force
    Write-Host "Removed draftly.db"
    Write-Host "Backup saved as: $bak"
    Write-Host ""
    Write-Host "Next: start the API again, then sign in with Google on Overview."
}
catch {
    Write-Host "Could not remove draftly.db (file may be locked)."
    Write-Host "Stop uvicorn first, then run this script again."
    Write-Host $_.Exception.Message
    exit 1
}
