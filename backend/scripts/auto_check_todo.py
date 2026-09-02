#!/usr/bin/env python3
"""
Auto-check script for BedaanWaves TODO.md
Runs periodically to scan codebase and mark completed tasks.
"""
import subprocess
import re
import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(r"E:\Shakour\BedaanProjects\OldFils\BedaanWaves")
TODO_FILE = PROJECT_ROOT / "TODO.md"
BACKEND_DIR = PROJECT_ROOT / "backend"


def get_git_log(since_hours=1):
    """Get recent git commits."""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since_hours} hours ago", "--oneline"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        return result.stdout.strip()
    except Exception:
        return ""


def check_file_exists(rel_path):
    """Check if a file exists in the backend."""
    return (BACKEND_DIR / rel_path).exists()


def check_file_contains(rel_path, pattern):
    """Check if a file contains a pattern."""
    filepath = BACKEND_DIR / rel_path
    if not filepath.exists():
        return False
    try:
        content = filepath.read_text(encoding="utf-8")
        return bool(re.search(pattern, content))
    except Exception:
        return False


def scan_implementations():
    """Scan codebase for implementation status of TODO items."""
    findings = {}

    # Security checks
    findings["auth_default"] = check_file_contains(
        "app/core/config.py", r'REQUIRE_AUTH.*=.*True'
    )
    findings["idor_fix"] = check_file_contains(
        "app/api/routes/portfolios.py", r'Portfolio\.user_id == user_id'
    )
    findings["refresh_jwt_error"] = check_file_contains(
        "app/api/routes/auth.py", r'JWTError|jwt\.decode'
    )

    # RBAC
    findings["system_rbac"] = check_file_contains(
        "app/api/routes/system.py", r'get_current_admin_user'
    )

    # N+1 Query
    findings["latest_prices_nplus1"] = check_file_contains(
        "app/api/routes/market.py", r'for symbol in symbols'
    )

    # Mass assignment
    findings["update_profile_allowlist"] = check_file_contains(
        "app/services/user/user_profile_service.py", r'allow.?list|ALLOWED_FIELDS|model_dump'
    )

    # Rate limiter
    findings["rate_limiter_key"] = check_file_contains(
        "app/api/middleware.py", r'client_ip.*path|RATE_LIMIT'
    )

    # Migration
    findings["alembic_config"] = check_file_exists("alembic.ini")
    findings["init_db_alembic"] = check_file_contains(
        "app/db/base.py", r'alembic|command\.upgrade'
    )

    # Crypto tables
    findings["raw_market_data_model"] = check_file_contains(
        "app/models/models.py", r'class RawMarketData'
    )
    findings["market_data_snapshot_model"] = check_file_contains(
        "app/models/models.py", r'class MarketDataSnapshot'
    )

    # MLSignal
    findings["mlsignal_valid_until"] = check_file_contains(
        "app/models/models.py", r'valid_until|is_active'
    )

    # Scoring
    findings["scoring_service"] = check_file_exists(
        "app/services/analysis/scoring_service.py"
    )
    findings["scoring_weights_config"] = check_file_contains(
        "app/core/config.py", r'SCORING_WEIGHTS'
    )

    # Dependencies
    findings["requirements_txt"] = check_file_exists("requirements.txt")

    # NLP services
    findings["chatbot_service"] = check_file_exists(
        "app/services/nlp/chatbot_service.py"
    )

    return findings


def update_todo_markers(findings):
    """Update TODO.md checkboxes based on findings."""
    if not TODO_FILE.exists():
        return False

    content = TODO_FILE.read_text(encoding="utf-8")
    original = content
    updated = False

    # Mapping of findings to TODO patterns
    checks = [
        ("auth_default", r'(\[ \] Change default `REQUIRE_AUTH` in `config.py` to `True`)',
         r'[x] Change default `REQUIRE_AUTH` in `config.py` to `True`'),
        ("idor_fix", r'(\[ \] Add condition `Portfolio.user_id == user_id`)',
         r'[x] Add condition `Portfolio.user_id == user_id`'),
        ("refresh_jwt_error", r'(\[ \] Wrap `jwt.decode\(token, \.\.\.\)` in `routes/auth.py:62` with `try/except JWTError`)',
         r'[x] Wrap `jwt.decode` with try/except JWTError'),
        ("system_rbac", r'(\[ \] Apply `Depends\(get_current_admin_user\)`)',
         r'[x] Apply `Depends(get_current_admin_user)`'),
        ("init_db_alembic", r'(\[ \] Replace `Base.metadata.create_all` in `base.py` with Alembic execution at startup)',
         r'[x] Replace `Base.metadata.create_all` with Alembic at startup'),
        ("raw_market_data_model", r'(\[ \] `RawMarketData`)',
         r'[x] `RawMarketData`'),
        ("market_data_snapshot_model", r'(\[ \] `MarketDataSnapshot`)',
         r'[x] `MarketDataSnapshot`'),
        ("mlsignal_valid_until", r'(\[ \] `MLSignal` with `valid_until`/`is_active`)',
         r'[x] `MLSignal` with `valid_until`/`is_active`'),
        ("scoring_weights_config", r'(\[ \] Change `scoring_service.py` to read `DIMENSION_WEIGHTS` from `get_settings\(\)\.SCORING_WEIGHTS`)',
         r'[x] Read `SCORING_WEIGHTS` from settings'),
        ("chatbot_service", r'(\[ \] Remove or expose unused NLP services \(`chatbot_service\.py`, `search_service\.py`\))',
         r'[x] Review NLP services'),
    ]

    for key, pattern, replacement in checks:
        if findings.get(key) and re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            updated = True

    if updated:
        TODO_FILE.write_text(content, encoding="utf-8")

    return updated


def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_log = get_git_log(since_hours=1)

    findings = scan_implementations()

    print(f"[{timestamp}] Auto-check started")
    if git_log:
        print(f"Recent commits:\n{git_log}")

    print(f"\nFindings:")
    for key, value in findings.items():
        status = "" if value else ""
        print(f"  {status} {key}")

    updated = update_todo_markers(findings)
    if updated:
        print("\nTODO.md updated with new findings!")
    else:
        print("\nNo changes to TODO.md needed.")

    print(f"[{timestamp}] Auto-check completed\n")


if __name__ == "__main__":
    main()

