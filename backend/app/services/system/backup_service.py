"""
Backup Service - Automated PostgreSQL Database Backup and Restore

Uses pg_dump for reliable database backups with configurable retention
and rotation policies.
"""

from __future__ import annotations

import asyncio
import gzip
import logging
import os
import secrets
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.utils import utc_now_iso
from app.services.core.base_service import BaseService

settings = get_settings()
logger = logging.getLogger(__name__)


class BackupService(BaseService):
    """
    Automated PostgreSQL backup service using pg_dump.

    Provides database backup and restore operations with:
    - pg_dump / psql integration for reliable PostgreSQL backups
    - Configurable backup directory and retention policy
    - Automatic backup rotation based on retention_days
    - Optional gzip compression
    """

    def __init__(
        self,
        backup_path: str | None = None,
        retention_days: int = 7,
        compression: bool = True,
    ) -> None:
        super().__init__("BackupService")
        self.backup_path = Path(backup_path) if backup_path else Path(settings.BACKUP_PATH)
        self.retention_days = retention_days
        self.compression = compression
        self._ongoing: dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """Create backup directory if it does not exist."""
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            "BackupService initialized path=%s retention=%dd compression=%s",
            self.backup_path,
            self.retention_days,
            self.compression,
        )

    async def shutdown(self) -> None:
        """Cancel any ongoing backup tasks."""
        for name, task in self._ongoing.items():
            task.cancel()
            self.logger.warning("Cancelled ongoing backup: %s", name)
        self.logger.info("BackupService shutdown")

    def _pg_env(self) -> dict[str, str]:
        env = os.environ.copy()
        password = settings.DB_PASSWORD or os.environ.get("PGPASSWORD", "")
        if password:
            env["PGPASSWORD"] = password
        return env

    def _pg_dump_args(self, output_file: Path) -> list[str]:
        return [
            "pg_dump",
            "-h",
            settings.DB_HOST,
            "-p",
            str(settings.DB_PORT),
            "-U",
            settings.DB_USER,
            "-d",
            settings.DB_NAME,
            "-f",
            str(output_file),
            "-F",
            "c",
            "--verbose",
        ]

    async def create_backup(self, name: str | None = None) -> dict[str, Any]:
        """
        Create a PostgreSQL database backup using pg_dump.

        Args:
            name: Optional backup name. Auto-generated timestamped name if omitted.

        Returns:
            Backup metadata including file path, size, and timestamp.

        Raises:
            RuntimeError: If pg_dump fails.
        """
        backup_name = name or f"backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        ext = ".dump.gz" if self.compression else ".dump"
        final_path = self.backup_path / f"{backup_name}{ext}"

        task = asyncio.create_task(self._run_pg_dump(final_path))
        self._ongoing[backup_name] = task

        try:
            await task
            await self._rotate_backups()
            size = final_path.stat().st_size if final_path.exists() else 0
            return {
                "backup_file": str(final_path),
                "name": backup_name,
                "timestamp": utc_now_iso(),
                "size": size,
                "compressed": self.compression,
                "status": "success",
            }
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.logger.error("Backup failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Backup failed: {exc}") from exc
        finally:
            self._ongoing.pop(backup_name, None)

    async def _run_pg_dump(self, output_path: Path) -> None:
        temp_path = output_path.with_suffix(".tmp")
        args = self._pg_dump_args(temp_path)
        env = self._pg_env()

        self.logger.info("Running pg_dump: %s", " ".join(args))

        def _run() -> None:
            result = subprocess.run(
                args,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"pg_dump failed (rc={result.returncode}): {result.stderr}"
                )
            if temp_path.exists():
                if self.compression:
                    with open(temp_path, "rb") as f_in:
                        with gzip.open(output_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    temp_path.unlink(missing_ok=True)
                else:
                    shutil.move(str(temp_path), str(output_path))

        await asyncio.to_thread(_run)
        self.logger.info("Backup completed: %s", output_path)

    async def restore_backup(self, backup_file: str) -> dict[str, Any]:
        """
        Restore a PostgreSQL database from a backup file.

        Args:
            backup_file: Path to the backup file (.dump or .dump.gz).

        Returns:
            Restore result metadata.

        Raises:
            FileNotFoundError: If backup file does not exist.
            RuntimeError: If psql restore fails.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        temp_path = backup_path
        if backup_path.suffix == ".gz":
            temp_path = backup_path.with_suffix("")
            with gzip.open(backup_path, "rb") as f_in:
                with open(temp_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        args = [
            "psql",
            "-h",
            settings.DB_HOST,
            "-p",
            str(settings.DB_PORT),
            "-U",
            settings.DB_USER,
            "-d",
            settings.DB_NAME,
            "-f",
            str(temp_path),
            "--verbose",
        ]
        env = self._pg_env()

        self.logger.info("Running psql restore: %s", " ".join(args))

        try:
            def _run() -> None:
                result = subprocess.run(
                    args,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"psql restore failed (rc={result.returncode}): {result.stderr}"
                    )

            await asyncio.to_thread(_run)
        finally:
            if temp_path != backup_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

        return {
            "status": "success",
            "backup_source": backup_file,
            "timestamp": utc_now_iso(),
        }

    async def _rotate_backups(self) -> None:
        """Remove backups older than retention_days."""
        cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)
        for file in self.backup_path.glob("*.dump*"):
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=UTC)
                if mtime < cutoff:
                    file.unlink(missing_ok=True)
                    self.logger.debug("Rotated old backup: %s", file.name)
            except Exception as exc:
                self.logger.warning("Failed to rotate backup %s: %s", file, exc)

    def list_backups(self) -> list[dict[str, Any]]:
        """List available backup files sorted by modification time (newest first)."""
        backups: list[dict[str, Any]] = []
        for file in sorted(
            self.backup_path.glob("*.dump*"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        ):
            backups.append(
                {
                    "file": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        file.stat().st_mtime, tz=UTC
                    ).isoformat(),
                }
            )
        return backups

    async def health_check(self) -> dict[str, Any]:
        """Return backup service health."""
        ongoing = list(self._ongoing.keys())
        return {
            "service": self.service_name,
            "status": "busy" if ongoing else "healthy",
            "ongoing_operations": ongoing,
            "backup_path": str(self.backup_path),
            "retention_days": self.retention_days,
            "compression": self.compression,
        }
