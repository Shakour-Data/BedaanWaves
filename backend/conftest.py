"""
Root-level conftest.py for BedaanWaves test suite.

Ensures the backend app package is importable and the .env file is loaded
before any application modules are imported, regardless of the working
directory from which pytest is invoked.
"""

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_BACKEND_DIR = _REPO_ROOT / "backend"

# Make the backend package importable as ``app`` from the repo root.
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Load environment variables from backend/.env (or repo-root .env) so that
# pydantic settings and other modules that read os.environ work in CI / tests.
def _load_env_file() -> None:
    env_path = _REPO_ROOT / ".env"
    if env_path.exists():
        env_path = env_path
    else:
        env_path = _BACKEND_DIR / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
    except Exception:
        # Fallback: manually parse simple KEY=VALUE lines
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                os.environ.setdefault(key, value)


_load_env_file()
