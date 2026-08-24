"""
Backup Service - Tier 9 System Service

Automated backup and recovery service for BedaanWaves platform.
Manages database, configuration, and state backups with configurable retention.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile

from ..core import BaseService


class BackupService(BaseService):
    """
    Automated backup service for BedaanWaves platform data.
    
    Provides backup and recovery operations for:
    - Database state and dumps
    - Configuration files
    - Platform state and metadata
    """
    
    def __init__(
        self,
        service_name: str = "BackupService",
        backup_dir: Optional[str] = None,
        retention_days: int = 7,
        compression: bool = True,
    ):
        super().__init__(service_name)
        self.backup_dir = Path(backup_dir) if backup_dir else Path("backups")
        self.retention_days = retention_days
        self.compression = compression
        self._ongoing_backups: Dict[str, asyncio.Task] = {}
        self._backup_history: List[Dict[str, Any]] = []
        
    async def initialize(self) -> None:
        """Initialize backup service."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"BackupService initialized with backup_dir={self.backup_dir}")
        
    async def shutdown(self) -> None:
        """Shutdown backup service."""
        self._cancel_all_backups()
        self.logger.info("BackupService shutdown")
        
    def _cancel_all_backups(self) -> None:
        """Cancel all ongoing backup operations."""
        for backup_type, task in self._ongoing_backups.items():
            task.cancel()
            self.logger.warning(f"Cancelled ongoing backup for {backup_type}")
        
    async def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention_days."""
        cutoff_date = datetime.now(timezone.utc)
        cutoff_date -= timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob("*.backup"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                self.logger.debug(f"Removed old backup: {backup_file.name}")
                
    async def backup_database(self, name: Optional[str] = None, _include_schema: bool = True) -> Dict[str, Any]:
        """
        Create database backup.
        
        Args:
            name: Optional backup name (auto-generated if not provided)
            _include_schema: Always True - includes schema and data
            
        Returns:
            Backup metadata
        """
        backup_name = name or f"db_backup_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Get database connection details
        from app.services.core.config_service import ConfigService
        config_service = ConfigService()
        db_config = {
            "host": config_service.get("DB_HOST"),
            "port": config_service.get("DB_PORT"),
            "database": config_service.get("DB_NAME"),
            "user": config_service.get("DB_USER"),
        }
        
        # Start backup task
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
        """Actually perform database backup operation."""
        backup_file = self.backup_dir / f"{name}.backup"
        
        try:
            import psycopg2
            from psycopg2.extras import DictCursor
            
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"],
                user=db_config["user"],
            )
            
            backup_data = {
                "metadata": {
                    "type": "database_backup",
                    "name": name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0",
                },
                "schema": {},
                "data": {},
            }
            
            if _include_schema:
                # Get table schemas
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    tables = cursor.fetchall()
                    
                    for table_tuple in tables:
                        table_name = table_tuple["table_name"]
                        backup_data["schema"][table_name] = {}
                        
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        columns = [desc[0] for desc in cursor.description]
                        backup_data["schema"][table_name]["columns"] = columns
                        
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        backup_data["schema"][table_name]["row_count"] = cursor.fetchone()[0]
            
            # Get table data
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                for table_tuple in tables:
                    table_name = table_tuple["table_name"]
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    backup_data["data"][table_name] = rows
            
            conn.close()
            
            # Compress if requested
            if self.compression:
                import gzip
                with open(f"{backup_file}.gz", "wb") as f:
                    with gzip.open(f, "wt", encoding="utf-8") as gz:
                        json.dump(backup_data, gz, default=str)
                backup_file = Path(f"{backup_file}.gz")
            else:
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, default=str)
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            return {
                "backup_file": str(backup_file),
                "name": name,
                "timestamp": datetime.now(timezone.utc),
                "size": backup_file.stat().st_size,
                "tables": len(backup_data["data"]),
                "status": "success",
            }
        except Exception as exc:
            self.logger.error(f"Database backup failed: {exc}", exc_info=True)
            raise
            
    async def backup_config(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create configuration backup.
        
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
        """Actually perform configuration backup operation."""
        backup_file = self.backup_dir / f"{name}.backup"
        
        try:
            # Collect all configuration files
            config_path = Path("backend/app/config")
            config_files = list(config_path.glob("*.py")) + list(config_path.glob("*.env")) + list(config_path.glob("*.json"))
            
            backup_data = {
                "metadata": {
                    "type": "config_backup",
                    "name": name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0",
                },
                "config_files": {},
            }
            
            for config_file in config_files:
                with open(config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    backup_data["config_files"][config_file.name] = content
            
            # Compress if requested
            if self.compression:
                import gzip
                with open(f"{backup_file}.gz", "wb") as f:
                    with gzip.open(f, "wt", encoding="utf-8") as gz:
                        json.dump(backup_data, gz, default=str)
                backup_file = Path(f"{backup_file}.gz")
            else:
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, default=str)
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            return {
                "backup_file": str(backup_file),
                "name": name,
                "timestamp": datetime.now(timezone.utc),
                "size": backup_file.stat().st_size,
                "files": len(backup_data["config_files"]),
                "status": "success",
            }
        except Exception as exc:
            self.logger.error(f"Configuration backup failed: {exc}", exc_info=True)
            raise
            
    async def create_platform_snapshot(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create platform state snapshot.
        
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
        """Actually perform platform snapshot operation."""
        backup_file = self.backup_dir / f"{name}.backup"
        
        try:
            # Collect platform state information
            from app.services.core.config_service import ConfigService
            from app.services.system.metrics_service import MetricsService
            
            config_service = ConfigService()
            metrics_service = MetricsService()
            
            snapshot_data = {
                "metadata": {
                    "type": "platform_snapshot",
                    "name": name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0",
                },
                "platform_state": {
                    "config": config_service.get_all(),
                    "metrics": metrics_service.get_all_metrics(),
                    "filesystem_snapshot": {},
                },
            }
            
            # Create filesystem snapshot
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
            
            # Compress if requested
            if self.compression:
                import gzip
                with open(f"{backup_file}.gz", "wb") as f:
                    with gzip.open(f, "wt", encoding="utf-8") as gz:
                        json.dump(snapshot_data, gz, default=str)
                backup_file = Path(f"{backup_file}.gz")
            else:
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(snapshot_data, f, default=str)
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            return {
                "backup_file": str(backup_file),
                "name": name,
                "timestamp": datetime.now(timezone.utc),
                "size": backup_file.stat().st_size,
                "directories": len(key_directories),
                "status": "success",
            }
        except Exception as exc:
            self.logger.error(f"Platform snapshot failed: {exc}", exc_info=True)
            raise
            
    async def restore_database(self, backup_file: str, _force: bool = False) -> Dict[str, Any]:
        """
        Restore from database backup.
        
        Args:
            backup_file: Path to backup file
            _force: Force restore, even if data exists
            
        Returns:
            Restore result metadata
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Load backup
        if backup_path.suffix == ".gz":
            import gzip
            with gzip.open(backup_path, "rt", encoding="utf-8") as f:
                backup_data = json.load(f)
        else:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
        
        # Validate backup
        if backup_data["metadata"]["type"] != "database_backup":
            raise ValueError(f"Invalid backup type: {backup_data['metadata']['type']}")
        
        try:
            import psycopg2
            from psycopg2.extras import DictCursor
            
            # Get database connection details
            from app.services.core.config_service import ConfigService
            config_service = ConfigService()
            
            conn = psycopg2.connect(
                host=config_service.get("DB_HOST"),
                port=config_service.get("DB_PORT"),
                database=config_service.get("DB_NAME"),
                user=config_service.get("DB_USER"),
            )
            
            # Restore schema
            for table_name, table_data in backup_data["schema"].items():
                with conn.cursor() as cursor:
                    # Create table
                    create_stmt = self._generate_create_table_stmt(table_name, table_data["columns"])
                    try:
                        cursor.execute(create_stmt)
                    except Exception:
                        self.logger.warning(f"Table {table_name} already exists, skipping recreation")
                        continue
                    
                    # Insert data if any
                    if table_data["row_count"] > 0:
                        placeholders = ", ".join(["%s"] * len(table_data["columns"]))
                        insert_stmt = f"INSERT INTO {table_name} VALUES ({placeholders})"
                        cursor.executemany(insert_stmt, [])
            
            # Restore data
            for table_name, table_data in backup_data["data"].items():
                with conn.cursor() as cursor:
                    placeholders = ", ".join(["%s"] * len(table_data[0]))
                    insert_stmt = f"INSERT INTO {table_name} VALUES ({placeholders})"
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
        column_definitions = []
        for i, column_name in enumerate(columns):
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
            "backup_history": self._backup_history[-10:],  # Last 10 operations
            "backup_dir": str(self.backup_dir),
            "retention_days": self.retention_days,
            "compression": self.compression,
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
        }