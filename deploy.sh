#!/usr/bin/env bash
# =============================================================================
# Universal Deployment Script for BedaanWaves
# Works on both Windows (via Git Bash/WLS) and Linux/macOS
# =============================================================================

set -e

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

log_info() { echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"; }
log_success() { echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"; }
log_warning() { echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"; }
log_error() { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"; }

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

check_command() {
    command -v "$1" >/dev/null 2>&1 || { log_error "Command '$1' not found!"; return 1; }
}

setup_windows() {
    log_info "Detected Windows environment"
    
    # Check for Docker Desktop
    if check_command "docker" && check_command "docker-compose"; then
        log_info "Docker found, using Docker Compose deployment"
        echo "docker-compose up -d --build"
        return 0
    fi
    
    log_error "Docker Desktop not found. Please install Docker Desktop for Windows"
    return 1
}

setup_linux() {
    log_info "Detected Linux environment"
    
    # Check for Docker
    if check_command "docker" && check_command "docker-compose"; then
        log_info "Docker found, using Docker Compose deployment"
        docker-compose up -d --build
        return 0
    fi
    
    # Check for docker-compose alternative
    if check_command "docker" && check_command "podman-compose"; then
        log_info "Podman found, using podman-compose"
        podman-compose up -d --build
        return 0
    fi
    
    log_info "Dockerfile found, installing dependencies locally"
    
    # Install Python dependencies
    if check_command "python3"; then
        log_info "Setting up Python environment..."
        python3 -m venv venv
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
        pip install --upgrade pip
        pip install -e .
    fi
    
    # Install Node.js dependencies
    if [[ -d "frontend" ]] && check_command "npm"; then
        log_info "Setting up Node.js environment..."
        cd frontend
        npm install --silent
        npm run build 2>/dev/null || log_warning "Frontend build skipped (development mode)"
        cd ..
    fi
    
    return 0
}

setup_macos() {
    log_info "Detected macOS environment"
    
    if check_command "docker" && check_command "docker-compose"; then
        log_info "Docker found, using Docker Compose deployment"
        docker-compose up -d --build
        return 0
    fi
    
    log_info "Installing dependencies locally..."
    
    if check_command "brew"; then
        log_info "Homebrew found, checking dependencies..."
        brew list python@3.11 >/dev/null 2>&1 || brew install python@3.11
        brew list redis >/dev/null 2>&1 || brew install redis
    fi
    
    return 0
}

deploy() {
    local os=$(detect_os)
    
    log_info "========================================"
    log_info "Starting BedaanWaves Universal Deployment"
    log_info "System detected: $os"
    log_info "========================================"
    
    # Create required directories
    mkdir -p data/archive logs models temp/uploads backend/test_protegration_phase2.py
    
    # Setup based on OS
    case "$os" in
        "windows")
            setup_windows
            ;;
        "linux")
            setup_linux
            ;;
        "macos")
            setup_macos
            ;;
        *)
            log_error "Unknown OS: $os"
            log_info "Please use Docker deployment instead"
            docker-compose up -d --build 2>/dev/null || exit 1
            ;;
    esac
    
    log_success "========================================"
    log_success "Deployment completed successfully!"
    log_success "========================================"
    echo ""
    echo "Services to start:"
    echo "  Backend:  uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "  Frontend: cd frontend && npm run dev -- --port 3005"
    echo ""
}

main() {
    if ! check_command "docker" 2>/dev/null && ! check_command "python3" 2>/dev/null && ! check_command "python" 2>/dev/null && ! check_command "npm" 2>/dev/null; then
        log_error "No deployment tool found!"
        log_error "Please install Docker, Python3, or Node.js first"
        exit 1
    fi
    
    deploy
}

main "$@"