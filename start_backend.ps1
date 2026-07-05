$ErrorActionPreference = "Stop"
$env:PYTHON_EXE = "C:\Users\ADARSH\AppData\Local\Programs\Python\Python314\python.exe"
Write-Host "Starting PRAVAAH Backend with FastAPI..." -ForegroundColor Cyan
cd C:\Users\ADARSH\Desktop\Bash\projects\PRAVAAH\backend
& $env:PYTHON_EXE -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
