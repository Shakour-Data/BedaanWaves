<#
.SYNOPSIS
  BedaänWaves - one-shot DB purification runner (no Docker, no password).

.DESCRIPTION
  Adds the PostgreSQL bin folder to PATH for this session, then:
    1. Pre-purge: pg_dump backup of the target database.
    2. Purge:    runs purification/purify_to_nasdaq.sql via psql.
    3. Verify:   runs purification/verify_purification.py.

  Authentication: uses the OS / pg_hba.conf method configured for
  localhost. On most Windows dev installs this is "trust" (no password).
  No password is read or stored. If your server does require a password,
  set PGPASSWORD in your environment before running.

.PARAMETER DbName
  Database to purify. Default: bedaanwaves_db

.PARAMETER User
  Postgres role. Default: postgres

.PARAMETER PgHost
  PostgreSQL host. Default: localhost

.PARAMETER PgPort
  PostgreSQL port. Default: 5432

.PARAMETER PgBin
  Path to the PostgreSQL bin folder containing psql.exe and pg_dump.exe.
  Default: 'C:\Program Files\PostgreSQL\17\bin'

.PARAMETER SkipBackup
  Skip the pre-purge pg_dump step (NOT recommended).

.EXAMPLE
  PS> .\purification\run_purge.ps1
  PS> .\purification\run_purge.ps1 -SkipBackup
  PS> $env:PGPASSWORD = 'secret'; .\purification\run_purge.ps1
#>

[CmdletBinding()]
param(
    [string]$DbName = 'bedaanwaves_db',
    [string]$User   = 'postgres',
    [string]$PgHost = 'localhost',
    [string]$PgPort = '5432',
    [string]$PgBin  = 'C:\Program Files\PostgreSQL\17\bin',
    [switch]$SkipBackup
)

$ErrorActionPreference = 'Stop'

$scriptPath = $PSCommandPath
if (-not $scriptPath) { $scriptPath = $MyInvocation.MyCommand.Path }
if (-not $scriptPath) { $scriptPath = (Get-Location).Path }
$purificationDir = Split-Path -Parent $scriptPath
$repoRoot       = Split-Path -Parent $purificationDir
$sqlFile        = Join-Path $purificationDir 'purify_to_nasdaq.sql'
$verify         = Join-Path $purificationDir 'verify_purification.py'
$backup         = Join-Path $purificationDir ("pre_purge_{0}_{1:yyyyMMdd_HHmmss}.dump" -f $DbName, (Get-Date))

if (-not (Test-Path -LiteralPath $PgBin)) {
    throw "PostgreSQL bin folder not found: $PgBin  (use -PgBin to override)"
}
foreach ($exe in 'psql.exe', 'pg_dump.exe') {
    $full = Join-Path $PgBin $exe
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Required tool not found: $full"
    }
}

# Put psql/pg_dump on PATH for this session only.
$env:Path = "$PgBin;$env:Path"
Write-Host "Using PostgreSQL: $PgBin" -ForegroundColor Cyan
Write-Host "Target: $PgHost`:$PgPort / db=$DbName / user=$User" -ForegroundColor Cyan
if (-not $env:PGPASSWORD) {
    Write-Host "Auth:   pg_hba.conf trust (no password)" -ForegroundColor DarkCyan
} else {
    Write-Host "Auth:   PGPASSWORD env var (hidden)" -ForegroundColor DarkCyan
}

# 1. Pre-purge backup
if (-not $SkipBackup) {
    Write-Host "`n[1/3] Pre-purge backup -> $backup" -ForegroundColor Yellow
    & pg_dump.exe -h $PgHost -p $PgPort -U $User -d $DbName -F c -f $backup
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed (exit $LASTEXITCODE)" }
    Write-Host "    OK" -ForegroundColor Green
} else {
    Write-Host "`n[1/3] Skipping pre-purge backup (-SkipBackup set)" -ForegroundColor DarkYellow
}

# 2. Purge
Write-Host "`n[2/3] Purge -> $sqlFile" -ForegroundColor Yellow
& psql.exe -h $PgHost -p $PgPort -U $User -d $DbName -v ON_ERROR_STOP=1 -f $sqlFile
if ($LASTEXITCODE -ne 0) { throw "psql purge failed (exit $LASTEXITCODE)" }
Write-Host "    OK" -ForegroundColor Green

# 3. Verify
Write-Host "`n[3/3] Verify -> $verify" -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql+psycopg://$User@$PgHost`:$PgPort/$DbName"
& python $verify
$verifyExit = $LASTEXITCODE
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue

if ($verifyExit -ne 0) {
    Write-Host ("`nVERIFY FAILED (exit {0}) - restore from backup if needed:" -f $verifyExit) -ForegroundColor Red
    Write-Host ("  pg_restore -h {0} -p {1} -U {2} -d {3} --clean --if-exists `"{4}`"" -f $PgHost, $PgPort, $User, $DbName, $backup) -ForegroundColor Red
    exit $verifyExit
}

Write-Host ("`nDONE - purification successful.") -ForegroundColor Green
Write-Host ("Backup retained at: {0}" -f $backup)
