"""
Data archival strategy for historical financial data - Implementation for TODO-I5
Implements long-term storage and archival of historical financial statements.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import hashlib
from enum import Enum
from app.services.core.base_service import DataService
from ...core.config import get_settings

class ArchivePolicy(Enum):
    """Data archival policies"""
    KEEP_ALL = "keep_all"
    KEEP_RECENT_5_YEARS = "keep_recent_5_years"
    KEEP_RECENT_10_YEARS = "keep_recent_10_years"
    KEEP_RECENT_3_YEARS = "keep_recent_3_years"

class DataArchivalService(DataService):
    """
    Data archival service for historical financial data
    Implements retention policies and archival strategies
    """
    
    def __init__(self,
                 service_name: str = "DataArchivalService"):
        super().__init__(service_name)
        self.settings = get_settings()
        self.policy = ArchivePolicy.KEEP_RECENT_5_YEARS
        self.archive_path = self.settings.ARCHIVE_PATH or "./data/archive"
        
        # Initialize archive storage
        self._archive_index = self._load_archive_index()
        
    async def initialize(self) -> None:
        """Initialize archival service"""
        self.logger.info(f"DataArchivalService initialized with policy: {self.policy.value}")
        
    async def shutdown(self) -> None:
        """Shutdown archival service"""
        self._save_archive_index()
        self.logger.info("DataArchivalService shutdown")
    
    def set_archive_policy(self, policy: ArchivePolicy) -> None:
        """Set the archival policy"""
        self.policy = policy
        self.logger.info(f"Archive policy set to: {policy.value}")
    
    async def archive_statement(self, statement_data: Dict) -> str:
        """
        Archive a financial statement to long-term storage
        Returns the archive identifier
        """
        # Generate unique archive ID
        archive_id = self._generate_archive_id(statement_data)
        
        # Create archive record
        archive_record = {
            "id": archive_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": statement_data.get("symbol", ""),
            "period": statement_data.get("period", ""),
            "statement_type": statement_data.get("statement_type", ""),
            "data_hash": self._compute_data_hash(statement_data),
            "archived_at": datetime.now().isoformat(),
            "policy_applied": self.policy.value,
        }
        
        # Store in archive index
        self._archive_index[archive_id] = archive_record
        
        # Persist to disk (simplified implementation)
        self._persist_archive(archive_id, statement_data)
        
        self.logger.info(f"Archived statement {archive_id} for {statement_data.get('symbol')}")
        return archive_id
    
    async def retrieve_archived_statement(self, archive_id: str) -> Optional[Dict]:
        """Retrieve an archived financial statement"""
        if archive_id not in self._archive_index:
            return None
        
        return self._load_archive(archive_id)
    
    async def get_historical_statements(
        self,
        symbol: str,
        statement_type: Optional[str] = None,
        years: int = 10
    ) -> List[Dict]:
        """
        Retrieve historical statements for a symbol within a time range
        """
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        results = []
        
        for archive_id, record in self._archive_index.items():
            if record.get("symbol") != symbol:
                continue
                
            if statement_type and record.get("statement_type") != statement_type:
                continue
            
            try:
                archived_date = datetime.fromisoformat(record.get("archived_at", ""))
                if archived_date >= cutoff_date:
                    statement = self._load_archive(archive_id)
                    if statement:
                        results.append(statement)
            except Exception as e:
                self.logger.error(f"Error retrieving {archive_id}: {e}")
        
        return results
    
    async def apply_retention_policy(self) -> Dict[str, int]:
        """
        Apply retention policy to archived data
        Returns summary of actions taken
        """
        removed_count = 0
        kept_count = 0
        cutoff_date = datetime.now() - timedelta(days=self._get_policy_days())
        
        to_remove = []
        for archive_id, record in self._archive_index.items():
            try:
                archived_date = datetime.fromisoformat(record.get("archived_at", ""))
                if archived_date < cutoff_date:
                    # Mark for removal based on policy
                    to_remove.append(archive_id)
                    removed_count += 1
                else:
                    kept_count += 1
            except Exception:
                continue
        
        # Remove marked archives
        for archive_id in to_remove:
            del self._archive_index[archive_id]
            self._delete_archive_file(archive_id)
        
        self.logger.info(f"Retention policy applied: {removed_count} removed, {kept_count} kept")
        return {
            "removed": removed_count,
            "kept": kept_count,
            "total": removed_count + kept_count
        }
    
    def _generate_archive_id(self, statement_data: Dict) -> str:
        """Generate a unique archive ID for a statement"""
        symbol = statement_data.get("symbol", "")
        period = statement_data.get("period", "")
        stmt_type = statement_data.get("statement_type", "")
        
        # Create hash-based ID
        content = f"{symbol}_{period}_{stmt_type}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _compute_data_hash(self, statement_data: Dict) -> str:
        """Compute hash of statement data for integrity verification"""
        content = json.dumps(statement_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_policy_days(self) -> int:
        """Get the number of days to keep based on policy"""
        policy_days = {
            ArchivePolicy.KEEP_ALL: 36500,  # 100 years
            ArchivePolicy.KEEP_RECENT_10_YEARS: 3650,
            ArchivePolicy.KEEP_RECENT_5_YEARS: 1825,
            ArchivePolicy.KEEP_RECENT_3_YEARS: 1095,
        }
        return policy_days.get(self.policy, 1825)
    
    def _load_archive_index(self) -> Dict:
        """Load archive index from storage"""
        index_file = Path(self.archive_path) / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load archive index: {e}")
        return {}

    def _save_archive_index(self) -> None:
        """Save archive index to storage"""
        index_file = Path(self.archive_path) / "index.json"
        try:
            Path(self.archive_path).mkdir(parents=True, exist_ok=True)
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(self._archive_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save archive index: {e}")

    def _persist_archive(self, archive_id: str, data: Dict) -> None:
        """Persist archive data to storage"""
        archive_file = Path(self.archive_path) / f"{archive_id}.json"
        try:
            with open(archive_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
        except Exception as e:
            self.logger.error(f"Failed to persist archive {archive_id}: {e}")

    def _load_archive(self, archive_id: str) -> Optional[Dict]:
        """Load archive data from storage"""
        archive_file = Path(self.archive_path) / f"{archive_id}.json"
        if archive_file.exists():
            try:
                with open(archive_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load archive {archive_id}: {e}")
        return None

    def _delete_archive_file(self, archive_id: str) -> None:
        """Delete archive file from storage"""
        archive_file = Path(self.archive_path) / f"{archive_id}.json"
        if archive_file.exists():
            try:
                archive_file.unlink()
            except Exception as e:
                self.logger.error(f"Failed to delete archive file {archive_id}: {e}")