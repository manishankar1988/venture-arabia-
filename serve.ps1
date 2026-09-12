# Runs the site in PRODUCTION mode on Windows using the Waitress WSGI server.
#
#   .\serve.ps1                       # uses .env.production (DEBUG=0)
#   .\serve.ps1 -EnvFile .env         # use another env file
#   .\serve.ps1 -Port 8080
#
# Before the first run:  copy .env.production.example .env.production  and fill it in.
# For a local test on plain HTTP set FORCE_HTTPS=0, SERVE_MEDIA=1 and ALLOWED_HOSTS=localhost,127.0.0.1
param(
    [string]$EnvFile = ".env.production",
    [int]$Port = 8000,
    [string]$ListenHost = "127.0.0.1",
    [int]$Threads = 8
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path $EnvFile)) {
    Write-Host "Env file '$EnvFile' not found. Copy .env.production.example to $EnvFile and fill it in." -ForegroundColor Red
    exit 1
}
$env:ENV_FILE = (Resolve-Path $EnvFile).Path

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -q -r requirements.txt
}

Write-Host "Checking production settings..." -ForegroundColor Cyan
.\.venv\Scripts\python manage.py check --deploy
.\.venv\Scripts\python manage.py migrate --noinput
.\.venv\Scripts\python manage.py collectstatic --noinput | Select-Object -Last 1

Write-Host ""
Write-Host "Serving in production mode on http://${ListenHost}:$Port  (env: $EnvFile)" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
.\.venv\Scripts\python -m waitress --listen="${ListenHost}:$Port" --threads=$Threads --url-scheme=http venture.wsgi:application
