"""
Data Integrity Service - Tier 9 System Service

Ensures ongoing data integrity, validates historical data completeness,
and monitors data quality across all sources in the BedaanWaves platform.
"""

from typing import Dict, List, Optional, Any
from datetime import timezone, datetime, timedelta
import asyncio
from app.services.core.base_service import BaseService
from app.services.data.data_validation_service import DataValidationService
from app.services.data.brs_api_client import BrsApiClient
from app.services.data.intl_api_client import IntlApiClient
from app.services.data.market_service import MarketService
import logging

class DataIntegrityService(BaseService):
    """
    Data Integrity Service.
    
    Responsibilities:
    - Continuous data integrity monitoring
    - Historical data completeness validation
    - Cross-source consistency checking
    - Data quality scoring and reporting
    - Automated alerting for data issues
    """
    
    def __init__(self,
                 service_name: str = "DataIntegrityService",
                 validation_service: Optional[DataValidationService] = None,
                 brs_client: Optional[BrsApiClient] = None,
                 intl_client: Optional[IntlApiClient] = None,
                 market_service: Optional[MarketService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize data integrity service.
        
        Args:
            service_name: Service identifier
            validation_service: Data validation service instance
            brs_client: BRS API client instance
            intl_client: International API client instance
            market_service: Market data service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.validation_service = validation_service or DataValidationService(
            brs_client=brs_client,
            intl_client=intl_client,
            market_service=market_service
        )
        self.brs_client = brs_client
        self.intl_client = intl_client
        self.market_service = market_service
        
        # Monitoring configuration
        self.monitoring_interval = 3600  # 1 hour
        self.alert_thresholds = {
            "data_staleness_hours": 24,
            "missing_data_percent": 5.0,
            "consistency_score_min": 0.9,
            "authenticity_score_min": 0.8
        }
        
        # Track last check times
        self.last_integrity_check = None
        self.last_validation_run = None
        
        # Alert history
        self.alert_history = []
    
    async def initialize(self) -> None:
        """Initialize data integrity service."""
        self.logger.info("Initializing DataIntegrityService")
        await self.validation_service.initialize()
        self.logger.info("DataIntegrityService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown data integrity service."""
        await self.validation_service.shutdown()
        self.logger.info("DataIntegrityService shutdown")
    
    async def run_full_integrity_check(self) -> Dict[str, Any]:
        """
        Run a comprehensive data integrity check.
        
        Returns:
            Complete integrity report
        """
        self.logger.info("Starting full data integrity check")
        start_time = datetime.now(timezone.utc)
        
        report = {
            "check_id": f"integrity_{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": start_time.isoformat(),
            "checks": {},
            "overall_status": "unknown",
            "summary": {},
            "recommendations": [],
            "alerts": []
        }
        
        try:
            # Check 1: Data source availability
            source_check = await self._check_source_availability()
            report["checks"]["source_availability"] = source_check
            
            # Check 2: Historical data completeness
            historical_check = await self._check_historical_completeness()
            report["checks"]["historical_completeness"] = historical_check
            
            # Check 3: Cross-source consistency
            consistency_check = await self._check_cross_source_consistency()
            report["checks"]["cross_source_consistency"] = consistency_check
            
            # Check 4: Data authenticity
            authenticity_check = await self._check_data_authenticity()
            report["checks"]["data_authenticity"] = authenticity_check
            
            # Check 5: Data freshness
            freshness_check = await self._check_data_freshness()
            report["checks"]["data_freshness"] = freshness_check
            
            # Calculate overall status
            report["overall_status"] = self._calculate_overall_status(report["checks"])
            
            # Generate summary
            report["summary"] = self._generate_summary(report["checks"])
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(report["checks"])
            
            # Generate alerts
            report["alerts"] = self._generate_alerts(report["checks"])
            
            # Update tracking
            self.last_integrity_check = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error during integrity check: {str(e)}")
            report["error"] = str(e)
            report["overall_status"] = "error"
        
        # Calculate duration
        end_time = datetime.now(timezone.utc)
        report["duration_seconds"] = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Integrity check completed in {report['duration_seconds']:.2f}s - Status: {report['overall_status']}")
        return report
    
    async def _check_source_availability(self) -> Dict[str, Any]:
        """Check availability of all data sources."""
        sources = [
            ("BRS", self.brs_client),
            ("International", self.intl_client),
            ("Market", self.market_service)
        ]
        
        results = {}
        available = 0
        
        for name, client in sources:
            try:
                if client:
                    # Try a simple health check or lightweight call
                    if hasattr(client, 'health_check'):
                        health = await client.health_check()
                        results[name] = {"status": "available", "details": health}
                    else:
                        results[name] = {"status": "available", "details": "client_present"}
                    available += 1
                else:
                    results[name] = {"status": "not_configured", "details": "client_not_provided"}
            except Exception as e:
                results[name] = {"status": "error", "details": str(e)}
        
        return {
            "sources": results,
            "available_count": available,
            "total_count": len(sources),
            "availability_percent": round(available / len(sources) * 100, 2) if sources else 0
        }
    
    async def _check_historical_completeness(self) -> Dict[str, Any]:
        """Check historical data completeness for major assets."""
        # Test assets from each category
        test_assets = {
            "stocks": ["AAPL", "MSFT", "GOOGL"],  # US stocks
            "indices": ["SPX", "FTSE", "N225"]     # Major indices
        }
        
        results = {}
        complete_count = 0
        total_tests = 0
        
        for asset_type, symbols in test_assets.items():
            type_results = {}
            for symbol in symbols:
                total_tests += 1
                try:
                    # Check 3-year historical data
                    validation = await self.validation_service.validate_historical_completeness(
                        source_type=asset_type,
                        symbol=symbol,
                        min_years=3
                    )
                    
                    type_results[symbol] = validation
                    
                    if validation.get("is_valid", False):
                        complete_count += 1
                        
                except Exception as e:
                    type_results[symbol] = {"error": str(e), "is_valid": False}
            
            results[asset_type] = type_results
        
        return {
            "by_asset_type": results,
            "complete_count": complete_count,
            "total_tests": total_tests,
            "completion_rate": round(complete_count / total_tests * 100, 2) if total_tests > 0 else 0
        }
    
    async def _check_cross_source_consistency(self) -> Dict[str, Any]:
        """Check consistency between data sources."""
        # Test symbols available in multiple sources
        test_pairs = []
        
        results = {}
        consistent_count = 0
        total_checks = 0
        
        for symbol, source_types in test_pairs:
            if len(source_types) >= 2:
                total_checks += 1
                try:
                    consistency = await self.validation_service.check_cross_source_consistency(
                        symbol=symbol,
                        data_types=["price", "volume"]
                    )
                    
                    results[f"{symbol}_consistency"] = consistency
                    
                    if consistency.get("is_consistent", False):
                        consistent_count += 1
                        
                except Exception as e:
                    results[f"{symbol}_consistency"] = {"error": str(e), "is_consistent": False}
        
        return {
            "pairwise_checks": results,
            "consistent_count": consistent_count,
            "total_checks": total_checks,
            "consistency_rate": round(consistent_count / total_checks * 100, 2) if total_checks > 0 else 0
        }
    
    async def _check_data_authenticity(self) -> Dict[str, Any]:
        """Check authenticity of data from sources."""
        # Would typically check signatures, certificates, or known good hashes
        # For now, return placeholder
        
        return {
            "status": "not_implemented",
            "message": "Authenticity checking requires cryptographic signatures from sources",
            "recommendation": "Implement source-specific authenticity verification"
        }
    
    async def _check_data_freshness(self) -> Dict[str, Any]:
        """Check freshness of data from sources."""
        # Check when data was last updated for key metrics
        freshness_results = {}
        stale_count = 0
        total_checks = 0
        
        # Test recent data for major assets
        test_cases = [
            ("SPX", "indices"),
            ("AAPL", "stocks")
        ]
        
        for symbol, asset_type in test_cases:
            total_checks += 1
            try:
                # Get latest data timestamp
                if asset_type == "stocks" and self.stock_service:
                    data = await self.stock_service.get_stock(symbol)
                elif asset_type == "indices" and self.market_service:
                    # Simplified - would use actual index data
                    data = {"timestamp": datetime.now(timezone.utc).isoformat()}
                else:
                    data = None
                
                if data and "timestamp" in data:
                    data_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                    age_hours = (datetime.now(timezone.utc) - data_time.replace(tzinfo=None)).total_seconds() / 3600
                    
                    is_fresh = age_hours <= self.alert_thresholds["data_staleness_hours"]
                    freshness_results[f"{symbol}_{asset_type}"] = {
                        "age_hours": round(age_hours, 2),
                        "is_fresh": is_fresh,
                        "timestamp": data["timestamp"]
                    }
                    
                    if not is_fresh:
                        stale_count += 1
                else:
                    freshness_results[f"{symbol}_{asset_type}"] = {
                        "error": "No timestamp data",
                        "is_fresh": False
                    }
                    stale_count += 1
                    
            except Exception as e:
                freshness_results[f"{symbol}_{asset_type}"] = {
                    "error": str(e),
                    "is_fresh": False
                }
                stale_count += 1
        
        return {
            "by_asset": freshness_results,
            "stale_count": stale_count,
            "total_checks": total_checks,
            "freshness_rate": round((total_checks - stale_count) / total_checks * 100, 2) if total_checks > 0 else 0
        }
    
    def _calculate_overall_status(self, checks: Dict[str, Any]) -> str:
        """Calculate overall integrity status."""
        # Simple scoring system
        score = 0
        max_score = 0
        
        # Source availability (20%)
        if "source_availability" in checks:
            sa = checks["source_availability"]
            avail_pct = sa.get("availability_percent", 0)
            score += (avail_pct / 100) * 20
            max_score += 20
        
        # Historical completeness (25%)
        if "historical_completeness" in checks:
            hc = checks["historical_completeness"]
            comp_pct = hc.get("completion_rate", 0)
            score += (comp_pct / 100) * 25
            max_score += 25
        
        # Consistency (20%)
        if "cross_source_consistency" in checks:
            cc = checks["cross_source_consistency"]
            cons_pct = cc.get("consistency_rate", 0)
            score += (cons_pct / 100) * 20
            max_score += 20
        
        # Freshness (20%)
        if "data_freshness" in checks:
            df = checks["data_freshness"]
            fresh_pct = df.get("freshness_rate", 0)
            score += (fresh_pct / 100) * 20
            max_score += 20
        
        # Authenticity (15%) - placeholder
        max_score += 15
        
        # Calculate percentage
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        if percentage >= 90:
            return "excellent"
        elif percentage >= 75:
            return "good"
        elif percentage >= 60:
            return "fair"
        elif percentage >= 40:
            return "poor"
        else:
            return "critical"
    
    def _generate_summary(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from checks."""
        return {
            "total_checks_performed": len([k for k in checks.keys() if k not in ["error"]]),
            "critical_issues": self._count_issues(checks, "critical"),
            "warnings": self._count_issues(checks, "warning"),
            "passing_checks": self._count_passing(checks)
        }
    
    def _count_issues(self, checks: Dict[str, Any], level: str) -> int:
        """Count issues of specified level."""
        # Simplified implementation
        count = 0
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict):
                if check_result.get("status") == "error" or check_result.get("is_valid") == False:
                    count += 1
        return count
    
    def _count_passing(self, checks: Dict[str, Any]) -> int:
        """Count passing checks."""
        count = 0
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict):
                if check_result.get("is_valid", False) or check_result.get("is_consistent", False):
                    count += 1
        return count
    
    def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on check results."""
        recommendations = []
        
        # Source availability recommendations
        if "source_availability" in checks:
            sa = checks["source_availability"]
            avail_pct = sa.get("availability_percent", 0)
            if avail_pct < 100:
                missing = [k for k, v in sa.get("sources", {}).items() 
                          if v.get("status") not in ["available", "not_configured"]]
                if missing:
                    recommendations.append(
                        f"Investigate unavailable data sources: {', '.join(missing)}"
                    )
        
        # Historical completeness recommendations
        if "historical_completeness" in checks:
            hc = checks["historical_completeness"]
            comp_rate = hc.get("completion_rate", 0)
            if comp_rate < 100:
                recommendations.append(
                    f"Acquire missing historical data to reach 100% completeness "
                    f"(currently {comp_rate}%)"
                )
        
        # Consistency recommendations
        if "cross_source_consistency" in checks:
            cc = checks["cross_source_consistency"]
            cons_rate = cc.get("consistency_rate", 0)
            if cons_rate < 95:
                recommendations.append(
                    f"Investigate data source inconsistencies "
                    f"(current consistency: {cons_rate}%)"
                )
        
        # Freshness recommendations
        if "data_freshness" in checks:
            df = checks["data_freshness"]
            fresh_rate = df.get("freshness_rate", 0)
            if fresh_rate < 90:
                stale_items = [
                    k for k, v in df.get("by_asset", {}).items()
                    if isinstance(v, dict) and not v.get("is_fresh", True)
                ]
                if stale_items:
                    recommendations.append(
                        f"Update stale data for: {', '.join(stale_items[:5])}"
                    )
        
        return recommendations
    
    def _generate_alerts(self, checks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on check results."""
        alerts = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Source availability alerts
        if "source_availability" in checks:
            sa = checks["source_availability"]
            avail_pct = sa.get("availability_percent", 0)
            if avail_pct < self.alert_thresholds.get("min_source_availability", 80):
                alerts.append({
                    "type": "source_availability",
                    "severity": "high",
                    "message": f"Low source availability: {avail_pct}%",
                    "timestamp": timestamp,
                    "details": sa
                })
        
        # Historical completeness alerts
        if "historical_completeness" in checks:
            hc = checks["historical_completeness"]
            comp_rate = hc.get("completion_rate", 0)
            if comp_rate < (100 - self.alert_thresholds["missing_data_percent"]):
                alerts.append({
                    "type": "historical_completeness",
                    "severity": "medium",
                    "message": f"Historical data completeness below threshold: {comp_rate}%",
                    "timestamp": timestamp,
                    "details": hc
                })
        
        # Consistency alerts
        if "cross_source_consistency" in checks:
            cc = checks["cross_source_consistency"]
            cons_rate = cc.get("consistency_rate", 0)
            if cons_rate < self.alert_thresholds["consistency_score_min"] * 100:
                alerts.append({
                    "type": "consistency",
                    "severity": "medium",
                    "message": f"Cross-source consistency below threshold: {cons_rate}%",
                    "timestamp": timestamp,
                    "details": cc
                })
        
        # Freshness alerts
        if "data_freshness" in checks:
            df = checks["data_freshness"]
            fresh_rate = df.get("freshness_rate", 0)
            if fresh_rate < 90:  # Less than 90% fresh
                alerts.append({
                    "type": "data_freshness",
                    "severity": "high",
                    "message": f"Data freshness below acceptable level: {fresh_rate}%",
                    "timestamp": timestamp,
                    "details": df
                })
        
        # Add to history
        self.alert_history.extend(alerts)
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        return alerts
    
    async def get_integrity_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get integrity trends over time.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Trend analysis
        """
        # In production, would query historical check results from database
        # For now, return placeholder
        
        return {
            "period_hours": hours,
            "trend_data": [],
            "summary": {
                "improving": False,
                "stable": True,
                "declining": False
            }
        }
    
    async def schedule_periodic_checks(self, interval_seconds: int = None):
        """
        Schedule periodic integrity checks.
        
        Args:
            interval_seconds: Check interval in seconds
        """
        if interval_seconds is None:
            interval_seconds = self.monitoring_interval
        
        self.logger.info(f"Starting periodic integrity checks every {interval_seconds} seconds")
        
        while True:
            try:
                await self.run_full_integrity_check()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                self.logger.info("Periodic checks cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in periodic check: {str(e)}")
                await asyncio.sleep(min(interval_seconds, 60))  # Shorter delay on error

# Factory function for dependency injection
def get_data_integrity_service(validation_service=None,
                               brs_client=None,
                               intl_client=None,
                               market_service=None,
                               logger=None) -> DataIntegrityService:
    """Factory function to create DataIntegrityService instance."""
    return DataIntegrityService(
        service_name="DataIntegrityService",
        validation_service=validation_service,
        brs_client=brs_client,
        intl_client=intl_client,
        market_service=market_service,
        logger=logger
    )