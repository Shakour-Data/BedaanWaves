"""
Backup Service - Tier 9 System Service

Automated backup and recovery service for BedaanWaves platform.
Manages database, configuration, and state backups with configurable retention,
encryption, and optional offsite storage.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import base64

from psycopg2 import sql

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from ..core import BaseService


class BackupService(BaseService):
    """
    Automated backup service for BedaanWaves platform data.
    
    Provides backup and recovery operations for:
    - Database state and dumps
    - Configuration files
    - Platform state and metadata
    
    Features:
    - AES-256 encryption via Fernet (symmetric)
    - Optional offsite storage via HTTP POST
    - Compression support
    - Configurable retention policy
    """
    
    def __init__(
        self,
        service_name: str = "BackupService",
        backup_dir: Optional[str] = None,
        retention_days: int = 7,
        compression: bool = True,
        config_service=None,
        metrics_service=None,
    ):
        super().__init__(service_name)
        self.backup_dir = Path(backup_dir) if backup_dir else Path("backups")
        self.retention_days = retention_days
        self.compression = compression
        self._ongoing_backups: Dict[str, asyncio.Task] = {}
        self._backup_history: List[Dict[str, Any]] = []
        self.config_service = config_service
        self.metrics_service = metrics_service
        self._fernet: Optional[Fernet] = None
        self._offsite_url: Optional[str] = None
        
    async def initialize(self) -> None:
        """Initialize backup service."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._fernet = self._create_fernet()
        self._offsite_url = os.environ.get("BACKUP_OFFSITE_URL")
        self.logger.info(
            f"BackupService initialized with backup_dir={self.backup_dir}, "
            f"encryption={'enabled' if self._fernet else 'disabled'}, "
            f"offsite={'enabled' if self._offsite_url else 'disabled'}"
        )
        
    async def shutdown(self) -> None:
        """Shutdown backup service."""
        self._cancel_all_backups()
        self.logger.info("BackupService shutdown")
        
    def _cancel_all_backups(self) -> None:
        """Cancel all ongoing backup operations."""
        for backup_type, task in self._ongoing_backups.items():
            task.cancel()
            self.logger.warning(f"Cancelled ongoing backup for {backup_type}")
    
    def _create_fernet(self) -> Optional[Fernet]:
        """Create Fernet cipher from configuration."""
        encryption_key = os.environ.get("BACKUP_ENCRYPTION_KEY")
        if not encryption_key:
            return None
        try:
            return Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as exc:
            self.logger.warning(f"Failed to initialize backup encryption: {exc}")
            return None
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a Fernet key from a password using PBKDF2."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using Fernet."""
        if not self._fernet:
            return data
        return self._fernet.encrypt(data)
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data using Fernet."""
        if not self._fernet:
            return data
        try:
            return self._fernet.decrypt(data)
        except InvalidToken as exc:
            self.logger.error(f"Backup decryption failed: {exc}")
            raise ValueError("Invalid backup encryption key or corrupted backup") from exc
    
    async def _upload_offsite(self, file_path: Path) -> Optional[str]:
        """Upload backup to offsite storage if configured."""
        if not self._offsite_url:
            return None
        try:
            import requests
            with open(file_path, "rb") as f:
                files = {"backup": (file_path.name, f, "application/octet-stream")}
                response = requests.post(
                    self._offsite_url,
                    files=files,
                    timeout=300,
                    headers={"X-Backup-Encrypted": str(self._fernet is not None).lower()},
                )
                response.raise_for_status()
                result = response.json()
                return result.get("url") or result.get("location")
        except Exception as exc:
            self.logger.warning(f"Offsite backup upload failed: {exc}")
            return None

    async def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention_days."""
        cutoff_date = datetime.now(timezone.utc)
        cutoff_date -= timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob("*.backup*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                self.logger.debug(f"Removed old backup: {backup_file.name}")
    
    async def _write_backup_file(self, backup_name: str, data: dict) -> tuple[Path, int]:
        """Write backup data to file with optional compression and encryption."""
        json_data = json.dumps(data, default=str).encode("utf-8")
        encrypted_data = self._encrypt_data(json_data)
        
        backup_file = self.backup_dir / f"{backup_name}.backup"
        if self.compression:
            import gzip
            final_path = Path(f"{backup_file}.gz")
            with open(final_path, "wb") as f:
                with gzip.open(f, "wt", encoding="utf-8") as gz:
                    gz.write(encrypted_data.decode("utf-8"))
        else:
            final_path = backup_file
            with open(final_path, "wb") as f:
                f.write(encrypted_data)
        
        return final_path, final_path.stat().st_size
    
    async def _read_backup_file(self, backup_file: Path) -> dict:
        """Read and decrypt backup data from file."""
        if backup_file.suffix == ".gz":
            import gzip
            with gzip.open(backup_file, "rt", encoding="utf-8") as f:
                encrypted_data = f.read().encode("utf-8")
        else:
            with open(backup_file, "rb") as f:
                encrypted_data = f.read()
        
        decrypted_data = self._decrypt_data(encrypted_data)
        return json.loads(decrypted_data)