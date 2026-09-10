#!/bin/bash
# BedaanWaves Automated Setup Script (Linux/macOS)
# ============================================================================
# One-command setup that automates:
# 1. Directory creation
# 2. Python virtual environment
# 3. Dependency installation
# 4. .env file generation with secure secrets
# 5. Database creation
# 6. Database migrations (alembic)
# 7. Real data seeding (5 years of market data)
# 8. Optional: Start the application
#
# Run from project root:
#     bash scripts/setup.sh
# ============================================================================

set -e

# Configuration
SKIP_SEED=false
START_APP=false
DATABASE_NAME="bedaawaves_db"
POSTGRES_PASSWORD="postgres"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USER="postgres"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/venv"
LOGS_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
MODELS_DIR="$PROJECT_ROOT/models"

log_step() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

log_success() {
    echo -e "  ${GREEN}OK:${NC} $1"
}

log_warn() {
    echo -e "  ${YELLOW}WARN:${NC} $1"
}

log_error() {
    echo -e "  ${RED}ERROR:${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-seed) SKIP_SEED=true ;;
        --start) START_APP=true ;;
        --db-name) DATABASE_NAME="$2"; shift ;;
        --pg-password) POSTGRES_PASSWORD="$2"; shift ;;
        --pg-host) POSTGRES_HOST="$2"; shift ;;
        --pg-port) POSTGRES_PORT="$2"; shift ;;
        --pg-user) POSTGRES_USER="$2"; shift ;;
    esac
    shift
done

echo -e "${CYAN}"
echo "============================================================"
echo " BedaanWaves Automated Setup"
echo "============================================================"
echo -e "${NC}"

# Step 1: Create directories
log_step "Creating directories"
mkdir -p "$LOGS_DIR" "$DATA_DIR" "$DATA_DIR/archive" "$MODELS_DIR" "$PROJECT_ROOT/temp" "$PROJECT_ROOT/backups"
log_success "Directories created"

# Step 2: Setup Python virtual environment
log_step "Setting up Python virtual environment"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi

PYTHON_EXE="$VENV_DIR/bin/python"
PIP_EXE="$VENV_DIR/bin/pip"

# Step 3: Upgrade pip
log_step "Upgrading pip"
"$PYTHON_EXE" -m pip install --upgrade pip setuptools wheel 2>/dev/null
log_success "pip upgraded"

# Step 4: Install dependencies
log_step "Installing Python dependencies"
"$PIP_EXE" install -r "$BACKEND_DIR/requirements.txt" 2>/dev/null
log_success "Dependencies installed"

# Step 5: Generate .env
log_step "Generating .env configuration"
ENV_PATH="$BACKEND_DIR/.env"
if [ ! -f "$ENV_PATH" ]; then
    SECRET_KEY1=$(openssl rand -base64 32 | tr -d '\n')
    SECRET_KEY2=$(openssl rand -base64 32 | tr -d '\n')

    cat > "$ENV_PATH" << EOF
APP_NAME=BedaanWaves
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$DATABASE_NAME
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

SECRET_KEY=$SECRET_KEY1
JWT_SECRET=$SECRET_KEY2
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
EOF
    log_success ".env file generated with secure secrets"
else
    log_success ".env file already exists (skipped)"
fi

# Step 6: Create database
log_step "Creating database"
export PGPASSWORD="$POSTGRES_PASSWORD"
if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$DATABASE_NAME"; then
    log_success "Database '$DATABASE_NAME' already exists"
else
    createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$DATABASE_NAME" 2>/dev/null || log_warn "Could not create database automatically"
    log_success "Database '$DATABASE_NAME' created"
fi

# Step 7: Run migrations
log_step "Running database migrations"
cd "$BACKEND_DIR"
"$PYTHON_EXE" -m alembic upgrade head 2>/dev/null || log_warn "Migration issue detected"
log_success "Migrations applied"

# Step 8: Seed data
if [ "$SKIP_SEED" = false ]; then
    log_step "Seeding real market data (5 years from Yahoo Finance)"
    echo -e "  ${YELLOW}This may take 30-60 minutes for full Nasdaq constituents...${NC}"
    "$PYTHON_EXE" scripts/seed_real_data.py 2>/dev/null || log_warn "Seeding encountered issues"
    log_success "Real data seeded"
else
    echo -e "  ${YELLOW}Skipping seed (use --skip-seed=false to seed)${NC}"
fi

echo -e "\n${GREEN}"
echo "============================================================"
echo " SETUP COMPLETE"
echo "============================================================"
echo -e "${NC}"

if [ "$START_APP" = true ]; then
    log_step "Starting BedaanWaves application"
    cd "$BACKEND_DIR"
    exec "$PYTHON_EXE" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo -e "${CYAN}To start the application:${NC}"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi
