# Starts the Venture Arabia website locally on http://127.0.0.1:8000/
# Usage:  right-click > Run with PowerShell, or from a terminal:  .\run.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -q --upgrade pip
    .\.venv\Scripts\python -m pip install -q -r requirements.txt
}
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example (DEBUG=1 for local use)." -ForegroundColor Yellow
}

# Start the local PostgreSQL server if the project is configured to use it
$envFile = Get-Content .env -ErrorAction SilentlyContinue
if ($envFile -match "^DATABASE_URL=postgres") {
    if (-not (Test-Path "D:\pgsql17\data")) { .\pg-local.ps1 init }
    $status = & .\pg-local.ps1 status 2>&1
    if ($status -notmatch "server is running") { .\pg-local.ps1 start }
}

.\.venv\Scripts\python manage.py migrate --noinput
.\.venv\Scripts\python manage.py seed_demo
.\.venv\Scripts\python manage.py attach_catalogue_images

Write-Host ""
Write-Host "Shop:  http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Admin: http://127.0.0.1:8000/manage/" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
