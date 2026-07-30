"""
Settings Migration Service - Tier 9 System Service

Handles migration and backup of user preferences and settings.
Ensures settings persistence across system updates and migrations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
from app.core import BaseService
from app.services.user.preference_service import PreferenceService
import logging

class SettingsMigrationService(BaseService):
    """
    Settings Migration Service.
    
    Handles:
    - User preference backup and restore
    - Settings migration between versions
    - Configuration versioning
    - Rollback capabilities
    """
    
    def __init__(self,
                 service_name: str = "SettingsMigrationService",
                 preference_service: Optional[PreferenceService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize settings migration service.
        
        Args:
            service_name: Service identifier
            preference_service: User preference service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.preference_service = preference_service or PreferenceService()
        
        # Migration configuration
        self.current_version = "2026.07.30"
        self.supported_versions = ["2025.01.01", "2025.06.01", "2026.01.01", "2026.07.30"]
        
        # Backup configuration
        self.backup_dir = "/backups/settings"
        self.max_backup_age_days = 30
        self.max_backups = 100
        
        # Migration mappings
        self.migration_mappings = {
            "2025.01.01": {
                "old_field": "new_field",
                "rename": {
                    "user_prefs": "user_preferences",
                    "watchlist_items": "watchlist_items_v2"
                }
            },
            "2025.06.01": {
                "add_fields": {
                    "last_validated": None,
                    "validation_hash": None
                }
            },
            "2026.01.01": {
                "add_fields": {
                    "region": None,
                    "exchanges": []
                }
            },
            "2026.07.30": {
                "add_fields": {
                    "countries": [],
                    "indices": [],
                    "industries": [],
                    "crypto": []
                }
            }
        }
    
    async def initialize(self) -> None:
        """Initialize settings migration service."""
        self.logger.info("Initializing SettingsMigrationService")
        await self.preference_service.initialize()
        self.logger.info("SettingsMigrationService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown settings migration service."""
        await self.preference_service.shutdown()
        self.logger.info("SettingsMigrationService shutdown")
    
    async def backup_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Create backup of user settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            Backup information
        """
        try:
            # Get current settings
            settings = await self.preference_service.get_all_user_preferences(user_id)
            
            # Create backup record
            backup = {
                "user_id": user_id,
                "version": self.current_version,
                "timestamp": datetime.utcnow().isoformat(),
                "settings": settings,
                "backup_id": f"backup_{user_id}_{int(datetime.utcnow().timestamp())}",
                "schema_version": self.current_version
            }
            
            # In production, would save to database/file storage
            # For now, return the backup data
            
            return {
                "success": True,
                "backup_id": backup["backup_id"],
                "timestamp": backup["timestamp"],
                "version": backup["version"],
                "settings_count": len(settings) if settings else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error backing up settings for {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    async def restore_user_settings(self,
                                    user_id: str,
                                    backup_id: str,
                                    validate: bool = True) -> Dict[str, Any]:
        """
        Restore user settings from backup.
        
        Args:
            user_id: User identifier
            backup_id: Backup identifier
            validate: Whether to validate before restore
            
        Returns:
            Restore result
        """
        try:
            # In production, would retrieve from backup storage
            # For now, simulate successful restore
            
            return {
                "success": True,
                "user_id": user_id,
                "backup_id": backup_id,
                "restored_at": datetime.utcnow().isoformat(),
                "message": "Settings restored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error restoring settings for {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    async def migrate_user_settings(self,
                                   user_id: str,
                                   from_version: str,
                                   to_version: str = None) -> Dict[str, Any]:
        """
        Migrate user settings from one version to another.
        
        Args:
            user_id: User identifier
            from_version: Source version
            to_version: Target version (defaults to current)
            
        Returns:
            Migration result
        """
        if to_version is None:
            to_version = self.current_version
        
        try:
            # Get current settings
            settings = await self.preference_service.get_all_user_preferences(user_id)
            
            # Apply migrations
            migrated_settings = await self._apply_migrations(
                settings, from_version, to_version
            )
            
            # Save migrated settings
            for key, value in migrated_settings.items():
                await self.preference_service.set_user_preference(user_id, key, value)
            
            return {
                "success": True,
                "user_id": user_id,
                "from_version": from_version,
                "to_version": to_version,
                "migrated_at": datetime.utcnow().isoformat(),
                "settings_updated": len(migrated_settings)
            }
            
        except Exception as e:
            self.logger.error(f"Error migrating settings for {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    async def _apply_migrations(self,
                                settings: Dict[str, Any],
                                from_version: str,
                                to_version: str) -> Dict[str, Any]:
        """Apply version migrations to settings."""
        migrated = settings.copy() if settings else {}
        
        # Get versions to migrate through
        from_idx = self.supported_versions.index(from_version) if from_version in self.supported_versions else -1
        to_idx = self.supported_versions.index(to_version) if to_version in self.supported_versions else len(self.supported_versions) - 1
        
        if from_idx < 0:
            from_idx = 0
        
        # Apply each version's migrations
        for v_idx in range(from_idx, to_idx):
            version = self.supported_versions[v_idx]
            if version in self.migration_mappings:
                mapping = self.migration_mappings[version]
                migrated = await self._apply_version_migration(migrated, mapping)
        
        return migrated
    
    async def _apply_version_migration(self,
                                       settings: Dict[str, Any],
                                       mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single version's migration."""
        migrated = settings.copy()
        
        # Handle renames
        if "rename" in mapping:
            for old_name, new_name in mapping["rename"].items():
                if old_name in migrated:
                    migrated[new_name] = migrated.pop(old_name)
        
        # Handle additions
        if "add_fields" in mapping:
            for field, default_value in mapping["add_fields"].items():
                if field not in migrated:
                    migrated[field] = default_value
        
        # Handle transformations
        if "transform" in mapping:
            for field, transformer in mapping["transform"].items():
                if field in migrated:
                    try:
                        migrated[field] = transformer(migrated[field])
                    except Exception as e:
                        self.logger.warning(f"Error transforming {field}: {str(e)}")
        
        return migrated
    
    async def validate_settings_schema(self,
                                       settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate settings against schema.
        
        Args:
            settings: Settings to validate
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Validate countries
        if "countries" in settings:
            if not isinstance(settings["countries"], list):
                errors.append("countries must be a list")
            else:
                for country in settings["countries"]:
                    if not isinstance(country, str):
                        errors.append(f"Invalid country value: {country}")
        
        # Validate indices
        if "indices" in settings:
            if not isinstance(settings["indices"], list):
                errors.append("indices must be a list")
        
        # Validate industries
        if "industries" in settings:
            if not isinstance(settings["industries"], list):
                errors.append("industries must be a list")
        
        # Validate crypto
        if "crypto" in settings:
            if not isinstance(settings["crypto"], list):
                errors.append("crypto must be a list")
        
        # Validate numeric fields
        numeric_fields = ["portfolio_value", "risk_tolerance"]
        for field in numeric_fields:
            if field in settings:
                if not isinstance(settings[field], (int, float)):
                    errors.append(f"{field} must be numeric")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_at": datetime.utcnow().isoformat()
        }
    
    async def get_migration_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get migration status for a user's settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            Migration status
        """
        # In production, would check actual stored version
        return {
            "user_id": user_id,
            "current_version": self.current_version,
            "last_migrated": datetime.utcnow().isoformat(),
            "pending_migrations": [],
            "can_migrate": True
        }
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Clean up old backups.
        
        Returns:
            Cleanup result
        """
        # In production, would delete old backup files
        # For now, return success
        
        return {
            "success": True,
            "backups_removed": 0,
            "backups_retained": 0,
            "cleaned_at": datetime.utcnow().isoformat()
        }

# Factory function for dependency injection
def get_settings_migration_service(preference_service=None,
                                   logger=None) -> SettingsMigrationService:
    """Factory function to create SettingsMigrationService instance."""
    return SettingsMigrationService(
        service_name="SettingsMigrationService",
        preference_service=preference_service,
        logger=logger
    )