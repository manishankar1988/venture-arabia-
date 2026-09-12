# Local PostgreSQL 17 for development (portable binaries, no admin rights needed).
#
#   .\pg-local.ps1 init     # first time: create the data folder, the 'venture' role and database
#   .\pg-local.ps1 start    # start the server on 127.0.0.1:5432
#   .\pg-local.ps1 stop     # stop the server
#   .\pg-local.ps1 status
#   .\pg-local.ps1 psql     # open a SQL prompt on the venture database
#
# Change $PgHome if the binaries live somewhere else. Production servers use
# their own PostgreSQL service (see README section 4).
param([Parameter(Position = 0)][string]$Action = "status")

$ErrorActionPreference = "Stop"
$PgHome = "D:\pgsql17\pgsql"
$DataDir = "D:\pgsql17\data"
$LogFile = "D:\pgsql17\postgres.log"
$Port = 5432
$Bin = Join-Path $PgHome "bin"
$env:PGPASSWORD = "postgres"   # superuser password set by init (local development only)

if (-not (Test-Path (Join-Path $Bin "pg_ctl.exe"))) {
    Write-Host "PostgreSQL binaries not found in $Bin." -ForegroundColor Red
    Write-Host "Download 'postgresql-17.x-windows-x64-binaries.zip' from https://www.enterprisedb.com/download-postgresql-binaries and extract it to D:\pgsql17"
    exit 1
}

switch ($Action) {
    "init" {
        if (Test-Path $DataDir) { Write-Host "Data directory already exists: $DataDir" -ForegroundColor Yellow; break }
        $pw = Join-Path $env:TEMP "pg_pw.txt"
        Set-Content -Path $pw -Value "postgres" -Encoding ascii -NoNewline
        & (Join-Path $Bin "initdb.exe") -D $DataDir -U postgres --pwfile=$pw -E UTF8 --locale=C -A scram-sha-256
        Remove-Item $pw
        & (Join-Path $Bin "pg_ctl.exe") -D $DataDir -l $LogFile -o "-p $Port" -w start
        & (Join-Path $Bin "psql.exe") -U postgres -h 127.0.0.1 -p $Port -c "CREATE ROLE venture LOGIN PASSWORD 'venture';"
        & (Join-Path $Bin "psql.exe") -U postgres -h 127.0.0.1 -p $Port -c "CREATE DATABASE venture OWNER venture ENCODING 'UTF8';"
        Write-Host "Database 'venture' created. DATABASE_URL=postgres://venture:venture@127.0.0.1:$Port/venture" -ForegroundColor Green
    }
    "start" {
        & (Join-Path $Bin "pg_ctl.exe") -D $DataDir -l $LogFile -o "-p $Port" -w start
    }
    "stop" {
        & (Join-Path $Bin "pg_ctl.exe") -D $DataDir -m fast -w stop
    }
    "status" {
        & (Join-Path $Bin "pg_ctl.exe") -D $DataDir status
    }
    "psql" {
        $env:PGPASSWORD = "venture"
        & (Join-Path $Bin "psql.exe") -U venture -h 127.0.0.1 -p $Port venture
    }
    default { Write-Host "Unknown action '$Action'. Use init | start | stop | status | psql" -ForegroundColor Red; exit 1 }
}
