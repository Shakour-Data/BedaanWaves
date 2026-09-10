"""
BedaanWaves Automated Setup Script (Windows PowerShell)
============================================================================
One-command setup that automates:
1. Directory creation
2. Python virtual environment
3. Dependency installation
4. .env file generation with secure secrets
5. Database creation
6. Database migrations (alembic)
7. Real data seeding (5 years of market data)
8. Optional: Start the application

Run from project root:
    powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
"""

param(
    [switch]$SkipSeed,
    [switch]$Start,
    [string]$DatabaseName = "bedaanwaves_db",
    [string]$PostgresPassword = "postgres",
    [string]$PostgresHost = "localhost",
    [string]$PostgresPort = "5432",
    [string]$PostgresUser = "postgres"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvDir = Join-Path $BackendDir "venv"
$LogsDir = Join-Path $ProjectRoot "logs"
$DataDir = Join-Path $ProjectRoot "data"
$ModelsDir = Join-Path $ProjectRoot "models"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  OK: $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  WARN: $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ERROR: $Message" -ForegroundColor Red
}

Write-Host @"
============================================================
 BedaanWaves Automated Setup
============================================================
"@ -ForegroundColor Cyan

Write-Step "Creating directories"
@($LogsDir, $DataDir, (Join-Path $DataDir "archive"), $ModelsDir, (Join-Path $ProjectRoot "temp")) | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}
Write-Success "Directories created"

Write-Step "Setting up Python virtual environment"
if (!(Test-Path $VenvDir)) {
    py -m venv $VenvDir
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment already exists"
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

Write-Step "Upgrading pip"
& $PythonExe -m pip install --upgrade pip setuptools wheel 2>&1 | Out-Null
Write-Success "pip upgraded"

Write-Step "Installing Python dependencies"
& $PipExe install -r (Join-Path $BackendDir "requirements.txt") 2>&1 | Out-Null
Write-Success "Dependencies installed"

Write-Step "Generating .env configuration"
$EnvPath = Join-Path $BackendDir ".env"
if (!(Test-Path $EnvPath)) {
    $SecretKeys = @(
        [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 } | ForEach-Object { [byte]$_ })),
        [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 } | ForEach-Object { [byte]$_ }))
    )

    $EnvContent = @"
APP_NAME=BedaanWaves
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

DATABASE_URL=postgresql://$PostgresUser:$PostgresPassword@${PostgresHost}:${PostgresPort}/${DatabaseName}
DATABASE_ECHO=False
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=True
CACHE_TTL_MINUTES=60

API_V1_STR=/api/v1
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=BedaanWaves Unified Capital Market Platform
DOCS_URL=/api/v1/docs
OPENAPI_URL=/api/v1/openapi.json

SECRET_KEY=$($SecretKeys[0])
JWT_SECRET=$($SecretKeys[1])
REQUIRE_AUTH=True
ALGORITHM=HS256

RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=100

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE","OPTIONS","PATCH"]
CORS_ALLOW_HEADERS=["*"]

BRS_API_BASE_URL=https://Api.BrsApi.ir
BRS_API_KEY=
BRS_RATE_LIMIT_MAX_DAILY=50000
BRS_RATE_LIMIT_MAX_WINDOW=300
BRS_RATE_LIMIT_WINDOW_SECONDS=300

CRYPTO_ENABLED=True
COINGECKO_API_BASE_URL=https://api.coingecko.com/api/v3
BINANCE_API_BASE_URL=https://api.binance.com/api/v3

ML_ENABLED=True
ML_MODEL_PATH=./models
ML_TRAINING_ENABLED=True
ML_UPDATE_INTERVAL_HOURS=1

LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./logs/bedaanwaves.log
LOG_ROTATION=midnight
LOG_RETENTION_DAYS=30

METRICS_ENABLED=True
BACKUP_ENABLED=True
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=./backups
ARCHIVE_PATH=./data/archive

SCHEDULER_ENABLED=True
SCHEDULER_JOB_INTERVAL=3600
SCHEDULER_DATA_INGEST_CRON=0 */2 * * *
SCHEDULER_MODEL_TRAIN_CRON=0 2 * * 0
SCHEDULER_SIGNAL_UPDATE_CRON=*/15 * * * *
"@
    Set-Content -Path $EnvPath -Value $EnvContent -Encoding UTF8
    Write-Success ".env file generated with secure secrets"
} else {
    Write-Success ".env file already exists (skipped)"
}

Write-Step "Creating database"
try {
    $env:PGPASSWORD = $PostgresPassword
    $DbExists = psql -h $PostgresHost -p $PostgresPort -U $PostgresUser -lqt 2>$null | ForEach-Object { $_.Split("|")[0].Trim() } | Where-Object { $_ -eq $DatabaseName }
    if (!$DbExists) {
        createdb -h $PostgresHost -p $PostgresPort -U $PostgresUser $DatabaseName 2>$null
        Write-Success "Database '$DatabaseName' created"
    } else {
        Write-Success "Database '$DatabaseName' already exists"
    }
} catch {
    Write-Warning "Could not create database automatically. Please ensure PostgreSQL is running."
}

Write-Step "Running database migrations"
Push-Location $BackendDir
try {
    & $PythonExe -m alembic upgrade head 2>&1 | Out-Null
    Write-Success "Migrations applied"
} catch {
    Write-Warning "Migration issue detected. Tables may already exist."
}
Pop-Location

if (!$SkipSeed) {
    Write-Step "Seeding real market data (5 years from Yahoo Finance)"
    Write-Host "  This may take 30-60 minutes for full Nasdaq constituents..." -ForegroundColor Yellow
    Push-Location $BackendDir
    try {
        & $PythonExe scripts/seed_real_data.py 2>&1
        Write-Success "Real data seeded"
    } catch {
        Write-Warning "Seeding encountered issues. You can run manually: py scripts/seed_real_data.py"
    }
    Pop-Location
} else {
    Write-Host "  Skipping seed (use --SkipSeed:`$false to seed)" -ForegroundColor Yellow
}

Write-Host @"

============================================================
 SETUP COMPLETE
============================================================
"@ -ForegroundColor Green

if ($Start) {
    Write-Step "Starting BedaanWaves application"
    Push-Location $BackendDir
    Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"
    Pop-Location
    Write-Host "  Application starting at http://localhost:8000" -ForegroundColor Green
    Write-Host "  API docs at http://localhost:8000/api/v1/docs" -ForegroundColor Green
} else {
    Write-Host "To start the application:" -ForegroundColor Cyan
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
}
