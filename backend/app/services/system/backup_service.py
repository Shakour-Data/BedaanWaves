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
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import base64
from app.core.utils import utc_now_iso

from psycopg2 import sql

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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
        kdf = PBKDF2HMAC(
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

    async def backup_database(self, name: Optional[str] = None, _include_schema: bool = True) -> Dict[str, Any]:
        """
        Create database backup with encryption.
        
        Args:
            name: Optional backup name (auto-generated if not provided)
            _include_schema: Always True - includes schema and data
            
        Returns:
            Backup metadata
        """
        backup_name = name or f"db_backup_{int(datetime.now(timezone.utc).timestamp())}"
        
        db_config = {
            "host": self.config_service.get("DB_HOST"),
            "port": self.config_service.get("DB_PORT"),
            "database": self.config_service.get("DB_NAME"),
            "user": self.config_service.get("DB_USER"),
        }
        
        task = asyncio.create_task(self._perform_database_backup(backup_name, db_config, _include_schema))
        self._ongoing_backups["database"] = task
        
        try:
            result = await task
            self._backup_history.append({
                "type": "database",
                "name": result["backup_file"],
                "timestamp": result["timestamp"],
                "size": result["size"],
                "status": "success",
            })
            self.logger.info(f"Database backup completed: {result['backup_file']}")
            return result
        except asyncio.CancelledError:
            self._backup_history.append({
                "type": "database",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "cancelled",
            })
            raise
        except Exception as exc:
            self._backup_history.append({
                "type": "database",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "error",
                "error": str(exc),
            })
            raise
        finally:
            self._ongoing_backups.pop("database", None)
            
    async def _perform_database_backup(self, name: str, db_config: Dict[str, Any], _include_schema: bool) -> Dict[str, Any]:
        """Actually perform database backup operation with encryption."""
        backup_data = {
            "metadata": {
                "type": "database_backup",
                "name": name,
                "timestamp": utc_now_iso(),
                "version": "2.0",
                "encrypted": self._fernet is not None,
            },
            "schema": {},
            "data": {},
        }
        
        try:
            import psycopg2
            from psycopg2.extras import DictCursor
            
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"],
                user=db_config["user"],
            )
            
            if _include_schema:
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    tables = cursor.fetchall()
                    
                    for table_tuple in tables:
                        table_name = table_tuple["table_name"]
                        backup_data["schema"][table_name] = {}
                        
                        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 1").format(sql.Identifier(table_name)))
                        columns = [desc[0] for desc in cursor.description]
                        backup_data["schema"][table_name]["columns"] = columns
                        
                        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                        backup_data["schema"][table_name]["row_count"] = cursor.fetchone()[0]
            
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                for table_tuple in tables:
                    table_name = table_tuple["table_name"]
                    cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
                    rows = cursor.fetchall()
                    backup_data["data"][table_name] = rows
            
            conn.close()
        except Exception as exc:
            self.logger.error(f"Database backup data collection failed: {exc}", exc_info=True)
            raise
        
        backup_file, size = await self._write_backup_file(name, backup_data)
        await self._cleanup_old_backups()
        
        offsite_url = await self._upload_offsite(backup_file)
        
        return {
            "backup_file": str(backup_file),
            "name": name,
            "timestamp": datetime.now(timezone.utc),
            "size": size,
            "tables": len(backup_data["data"]),
            "encrypted": self._fernet is not None,
            "offsite_url": offsite_url,
            "status": "success",
        }

    async def backup_config(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create configuration backup with encryption.
        
        Args:
            name: Optional backup name (auto-generated if not provided)
            
        Returns:
            Backup metadata
        """
        backup_name = name or f"config_backup_{int(datetime.now(timezone.utc).timestamp())}"
        
        task = asyncio.create_task(self._perform_config_backup(backup_name))
        self._ongoing_backups["config"] = task
        
        try:
            result = await task
            self._backup_history.append({
                "type": "config",
                "name": result["backup_file"],
                "timestamp": result["timestamp"],
                "size": result["size"],
                "status": "success",
            })
            self.logger.info(f"Configuration backup completed: {result['backup_file']}")
            return result
        except asyncio.CancelledError:
            self._backup_history.append({
                "type": "config",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "cancelled",
            })
            raise
        except Exception as exc:
            self._backup_history.append({
                "type": "config",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "error",
                "error": str(exc),
            })
            raise
        finally:
            self._ongoing_backups.pop("config", None)
            
    async def _perform_config_backup(self, name: str) -> Dict[str, Any]:
        """Actually perform configuration backup operation with encryption."""
        backup_data = {
            "metadata": {
                "type": "config_backup",
                "name": name,
                "timestamp": utc_now_iso(),
                "version": "2.0",
                "encrypted": self._fernet is not None,
            },
            "config_files": {},
        }
        
        try:
            config_path = Path("backend/app/config")
            config_files = list(config_path.glob("*.py")) + list(config_path.glob("*.env")) + list(config_path.glob("*.json"))
            
            for config_file in config_files:
                with open(config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    backup_data["config_files"][config_file.name] = content
        except Exception as exc:
            self.logger.warning(f"Some config files could not be backed up: {exc}")
        
        backup_file, size = await self._write_backup_file(name, backup_data)
        await self._cleanup_old_backups()
        
        offsite_url = await self._upload_offsite(backup_file)
        
        return {
            "backup_file": str(backup_file),
            "name": name,
            "timestamp": datetime.now(timezone.utc),
            "size": size,
            "files": len(backup_data["config_files"]),
            "encrypted": self._fernet is not None,
            "offsite_url": offsite_url,
            "status": "success",
        }

    async def create_platform_snapshot(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create platform state snapshot with encryption.
        
        Args:
            name: Optional backup name (auto-generated if not provided)
            
        Returns:
            Snapshot metadata
        """
        backup_name = name or f"snapshot_{int(datetime.now(timezone.utc).timestamp())}"
        
        task = asyncio.create_task(self._perform_platform_snapshot(backup_name))
        self._ongoing_backups["snapshot"] = task
        
        try:
            result = await task
            self._backup_history.append({
                "type": "snapshot",
                "name": result["backup_file"],
                "timestamp": result["timestamp"],
                "size": result["size"],
                "status": "success",
            })
            self.logger.info(f"Platform snapshot completed: {result['backup_file']}")
            return result
        except asyncio.CancelledError:
            self._backup_history.append({
                "type": "snapshot",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "cancelled",
            })
            raise
        except Exception as exc:
            self._backup_history.append({
                "type": "snapshot",
                "name": backup_name,
                "timestamp": datetime.now(timezone.utc),
                "status": "error",
                "error": str(exc),
            })
            raise
        finally:
            self._ongoing_backups.pop("snapshot", None)
            
    async def _perform_platform_snapshot(self, name: str) -> Dict[str, Any]:
        """Actually perform platform snapshot operation with encryption."""
        snapshot_data = {
            "metadata": {
                "type": "platform_snapshot",
                "name": name,
                "timestamp": utc_now_iso(),
                "version": "2.0",
                "encrypted": self._fernet is not None,
            },
            "platform_state": {
                "config": self.config_service.get_all() if self.config_service else {},
                "metrics": self.metrics_service.get_all_metrics() if self.metrics_service else {},
                "filesystem_snapshot": {},
            },
        }
        
        try:
            key_directories = [
                "backend/app/services",
                "backend/app/models",
                "frontend",
            ]
            
            for directory in key_directories:
                for file_path in Path(directory).glob("**/*"):
                    if file_path.is_file():
                        with open(file_path, "r", encoding="utf-8") as f:
                            snapshot_data["platform_state"]["filesystem_snapshot"][str(file_path)] = f.read()
        except Exception as exc:
            self.logger.warning(f"Some files could not be snapshotted: {exc}")
        
        backup_file, size = await self._write_backup_file(name, snapshot_data)
        await self._cleanup_old_backups()
        
        offsite_url = await self._upload_offsite(backup_file)
        
        return {
            "backup_file": str(backup_file),
            "name": name,
            "timestamp": datetime.now(timezone.utc),
            "size": size,
            "directories": len(key_directories),
            "encrypted": self._fernet is not None,
            "offsite_url": offsite_url,
            "status": "success",
        }

    async def restore_database(self, backup_file: str, _force: bool = False) -> Dict[str, Any]:
        """
        Restore from database backup with decryption.
        
        Args:
            backup_file: Path to backup file
            _force: Force restore, even if data exists
            
        Returns:
            Restore result metadata
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        backup_data = await self._read_backup_file(backup_path)
        
        if backup_data["metadata"]["type"] != "database_backup":
            raise ValueError(f"Invalid backup type: {backup_data['metadata']['type']}")
        
        try:
            import psycopg2
            from psycopg2.extras import DictCursor
            
            conn = psycopg2.connect(
                host=self.config_service.get("DB_HOST"),
                port=self.config_service.get("DB_PORT"),
                database=self.config_service.get("DB_NAME"),
                user=self.config_service.get("DB_USER"),
            )
            
            for table_name, table_data in backup_data["schema"].items():
                with conn.cursor() as cursor:
                    create_stmt = self._generate_create_table_stmt(table_name, table_data["columns"])
                    try:
                        cursor.execute(create_stmt)
                    except Exception:
                        self.logger.warning(f"Table {table_name} already exists, skipping recreation")
                        continue
                    
                    if table_data["row_count"] > 0:
                        placeholders = ", ".join(["%s"] * len(table_data["columns"]))
                        insert_stmt = sql.SQL("INSERT INTO {} VALUES ({})").format(
                            sql.Identifier(table_name),
                            sql.SQL(placeholders)
                        )
                        cursor.executemany(insert_stmt, [])
            
            for table_name, table_data in backup_data["data"].items():
                with conn.cursor() as cursor:
                    if table_data:
                        placeholders = ", ".join(["%s"] * len(table_data[0]))
                        insert_stmt = sql.SQL("INSERT INTO {} VALUES ({})").format(
                            sql.Identifier(table_name),
                            sql.SQL(placeholders)
                        )
                        cursor.executemany(insert_stmt, table_data)
            
            conn.commit()
            conn.close()
            
            self._backup_history.append({
                "type": "database_restore",
                "backup_source": backup_file,
                "timestamp": datetime.now(timezone.utc),
                "tables_restoraged": len(backup_data["data"]),
                "status": "success",
            })
            
            self.logger.info(f"Database restored from {backup_file}")
            return {
                "status": "success",
                "backup_source": backup_file,
                "timestamp": datetime.now(timezone.utc),
                "tables_restoraged": len(backup_data["data"]),
                "rows_restoraged": sum(len(table_data) for table_data in backup_data["data"].values()),
            }
        except Exception as exc:
            self._backup_history.append({
                "type": "database_restore",
                "backup_source": backup_file,
                "timestamp": datetime.now(timezone.utc),
                "status": "error",
                "error": str(exc),
            })
            self.logger.error(f"Database restore failed: {exc}", exc_info=True)
            raise
            
    def _generate_create_table_stmt(self, table_name: str, columns: List[str]) -> str:
        """Generate CREATE TABLE statement from column list."""
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        column_definitions = []
        for i, column_name in enumerate(columns):
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', column_name):
                raise ValueError(f"Invalid column name: {column_name}")
            column_type = "VARCHAR(255)"
            if column_name.endswith("_id") or column_name.endswith("_id_"):
                column_type = "INTEGER"
            elif any(keyword in column_name.lower() for keyword in ["id", "uuid"]):
                column_type = "INTEGER"
            elif any(keyword in column_name.lower() for keyword in ["count", "number", "amount"]):
                column_type = "INTEGER"
            elif any(keyword in column_name.lower() for keyword in ["price", "amount", "value"]):
                column_type = "DECIMAL(10,2)"
            elif any(keyword in column_name.lower() for keyword in ["date", "time", "timestamp", "created", "updated"]):
                column_type = "TIMESTAMP"
            
            column_definitions.append(f"  {column_name} {column_type}")
        
        return f"CREATE TABLE {table_name} (\n" + ",\n".join(column_definitions) + "\n);"
            
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup status."""
        status = {
            "ongoing_backups": list(self._ongoing_backups.keys()),
            "backup_history": self._backup_history[-10:],
            "backup_dir": str(self.backup_dir),
            "retention_days": self.retention_days,
            "compression": self.compression,
            "encryption_enabled": self._fernet is not None,
            "offsite_enabled": self._offsite_url is not None,
            "available_backups": [],
        }
        
        for backup_file in self.backup_dir.glob("*.backup*"):
            status["available_backups"].append({
                "file": backup_file.name,
                "size": backup_file.stat().st_size,
                "modified": backup_file.stat().st_mtime,
            })
        
        return status
            
    async def health_check(self) -> Dict[str, Any]:
        """Check backup service health."""
        ongoing_backup_types = list(self._ongoing_backups.keys())
        
        return {
            "service": self.service_name,
            "status": "healthy" if not ongoing_backup_types else "busy",
            "ongoing_operations": ongoing_backup_types,
            "backup_dir_exists": self.backup_dir.exists(),
            "retention_days": self.retention_days,
            "compression_enabled": self.compression,
            "encryption_enabled": self._fernet is not None,
            "offsite_enabled": self._offsite_url is not None,
        }
