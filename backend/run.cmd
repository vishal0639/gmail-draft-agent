@echo off
setlocal
cd /d %~dp0

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
  goto :eof
)

echo .venv not found. Creating venv + installing requirements...
python -m venv .venv
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

