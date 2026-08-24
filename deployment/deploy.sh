#!/usr/bin/env bash
# =============================================================================
# Universal Deployment Script for BedaanWaves
# Direct server deployment - no Docker
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

setup_linux() {
    log_info "Detected Linux environment"
    
    log_info "Installing dependencies locally"
    
    # Install Python dependencies
    if check_command "python3"; then
        log_info "Setting up Python environment..."
        python3 -m venv venv
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
        pip install --upgrade pip
        pip install -r backend/requirements.txt
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
    
    log_info "Installing dependencies locally..."
    
    if check_command "brew"; then
        log_info "Homebrew found, checking dependencies..."
        brew list python@3.11 >/dev/null 2>&1 || brew install python@3.11
        brew list redis >/dev/null 2>&1 || brew install redis
    fi
    
    return 0
}

setup_windows() {
    log_info "Detected Windows environment"
    
    log_info "Setting up Windows environment..."
    
    if check_command "py"; then
        log_info "Python found, setting up environment..."
        py -m venv backend/venv
        cd backend
        .\venv\Scripts\activate
        py -m pip install --upgrade pip
        pip install -r requirements.txt
        cd ..
    fi
    
    if [[ -d "frontend" ]] && check_command "npm"; then
        log_info "Setting up Node.js environment..."
        cd frontend
        npm install --silent
        npm run build 2>/dev/null || log_warning "Frontend build skipped (development mode)"
        cd ..
    fi
    
    return 0
}

deploy() {
    local os=$(detect_os)
    
    log_info "========================================"
    log_info "Starting BedaanWaves Direct Deployment"
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
            log_info "Please use Linux, macOS, or Windows for deployment"
            return 1
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
    if ! check_command "python3" 2>/dev/null && ! check_command "python" 2>/dev/null && ! check_command "npm" 2>/dev/null; then
        log_error "No deployment tool found!"
        log_error "Please install Python3 or Node.js first"
        exit 1
    fi
    
    deploy
}

main "$@"
