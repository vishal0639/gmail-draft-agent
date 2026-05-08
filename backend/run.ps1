$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Host ".venv not found. Creating venv + installing requirements..." -ForegroundColor Yellow
  python -m venv .venv
  & $python -m pip install -r requirements.txt
}

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

