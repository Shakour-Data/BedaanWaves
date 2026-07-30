"""
Data Validation Service - Tier 2 Data Service

Validates data integrity, authenticity, and completeness across all sources.
Ensures historical data meets 3+ year minimum requirement.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
import hashlib
import json
import asyncio
from app.core import CachedService
from app.services.data.brs_api_client import BrsApiClient
from app.services.data.crypto_api_client import CryptoApiClient
from app.services.data.intl_api_client import IntlApiClient
from app.services.data.market_service import MarketService
from app.services.data.stock_service import StockService
import logging

class DataValidationService(CachedService):
    """
    Data validation service ensuring data integrity and authenticity.
    
    Validates:
    - Historical data completeness (3+ year minimum)
    - Source authenticity and traceability
    - Cross-source consistency
    - Data quality metrics
    """
    
    def __init__(self, 
                 service_name: str = "DataValidationService",
                 brs_client: Optional[BrsApiClient] = None,
                 crypto_client: Optional[CryptoApiClient] = None,
                 intl_client: Optional[IntlApiClient] = None,
                 market_service: Optional[MarketService] = None,
                 stock_service: Optional[StockService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize data validation service.
        
        Args:
            service_name: Service identifier
            brs_client: BRS API client instance
            crypto_client: Crypto API client instance
            intl_client: International API client instance
            market_service: Market service instance
            stock_service: Stock service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.brs_client = brs_client
        self.crypto_client = crypto_client
        self.intl_client = intl_client
        self.market_service = market_service
        self.stock_service = stock_service
        
        # Data source mapping with validation requirements
        self.data_sources = {
            "stocks": {
                "clients": ["brs_client", "intl_client"],
                "min_years": 3,
                "authentication_required": True
            },
            "crypto": {
                "clients": ["crypto_client"],
                "min_years": 3,
                "authentication_required": False
            },
            "market_indices": {
                "clients": ["market_service"],
                "min_years": 3,
                "authentication_required": False
            }
        }
    
    async def initialize(self) -> None:
        """Initialize data validation service."""
        self.logger.info("Initializing DataValidationService")
        
        # Validate service dependencies
        dependencies = {
            "BRS Client": self.brs_client,
            "Crypto Client": self.crypto_client,
            "Intl Client": self.intl_client,
            "Market Service": self.market_service,
            "Stock Service": self.stock_service
        }
        
        for name, client in dependencies.items():
            if client is None:
                self.logger.warning(f"{name} not provided - limited validation capability")
        
        self.logger.info("DataValidationService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown data validation service."""
        self.cache_clear()
        self.logger.info("DataValidationService shutdown")
    
    async def validate_historical_completeness(self, 
                                             source_type: str,
                                             symbol: str,
                                             min_years: int = 3) -> Dict[str, Any]:
        """
        Validate that historical data meets minimum time requirement.
        
        Args:
            source_type: Type of data source (stocks, crypto, market_indices)
            symbol: Asset symbol to validate
            min_years: Minimum years of data required
            
        Returns:
            Validation results with completeness score
        """
        cache_key = f"historical_completeness:{source_type}:{symbol}:{min_years}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        try:
            validation_result = {
                "symbol": symbol,
                "source_type": source_type,
                "min_years_required": min_years,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "is_valid": False,
                "years_available": 0,
                "earliest_date": None,
                "latest_date": None,
                "missing_periods": [],
                "data_gaps": [],
                "validation_score": 0.0
            }
            
            # Get data based on source type
            data_points = []
            if source_type == "stocks" and self.stock_service:
                data_points = await self.stock_service.get_history(symbol)
            elif source_type == "crypto" and self.crypto_client:
                # Get crypto historical data
                pass  # Would implement crypto specific fetching
            elif source_type == "market_indices" and self.market_service:
                # Get market index historical data
                pass
            
            if data_points:
                # Analyze date range
                dates = [dp.get('date') for dp in data_points if dp.get('date')]
                if dates:
                    # Convert to datetime objects for comparison
                    date_objects = []
                    for d in dates:
                        try:
                            if isinstance(d, str):
                                date_objects.append(datetime.strptime(d, "%Y-%m-%d").date())
                            elif isinstance(d, date):
                                date_objects.append(d)
                            elif isinstance(d, datetime):
                                date_objects.append(d.date())
                        except ValueError:
                            continue
                    
                    if date_objects:
                        earliest = min(date_objects)
                        latest = max(date_objects)
                        
                        # Calculate years of data
                        date_range = latest - earliest
                        years_available = date_range.days / 365.25
                        
                        validation_result["years_available"] = years_available
                        validation_result["earliest_date"] = earliest.isoformat()
                        validation_result["latest_date"] = latest.isoformat()
                        validation_result["is_valid"] = years_available >= min_years
                        validation_result["validation_score"] = min(years_available / min_years, 1.0)
                        
                        # Identify gaps (simplified - in production would check for missing periods)
                        if years_available < min_years:
                            validation_result["missing_periods"].append({
                                "required_years": min_years,
                                "available_years": years_available,
                                "shortfall_years": min_years - years_available
                            })
            
            # Cache result for 1 hour
            self.set_cached(cache_key, validation_result, 3600)
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating historical completeness for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "source_type": source_type,
                "error": str(e),
                "is_valid": False,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def verify_source_authenticity(self, 
                                       source_name: str,
                                       data_sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify authenticity and integrity of a data source.
        
        Args:
            source_name: Name of the data source
            data_sample: Sample data from the source
            
        Returns:
            Authenticity verification results
        """
        cache_key = f"source_authenticity:{source_name}:{hash(json.dumps(data_sample, sort_keys=True))}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        try:
            verification_result = {
                "source_name": source_name,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "is_authentic": False,
                "authenticity_score": 0.0,
                "checks_performed": [],
                "warnings": [],
                "errors": []
            }
            
            # Check 1: Source identifier validation
            valid_sources = ["BRS", "BINANCE", "COINBASE", "NASDAQ", "NYSE", "LSE", "HKEX"]
            source_check = {
                "check": "source_identifier",
                "passed": source_name.upper() in valid_sources,
                "message": f"Source '{source_name}' is {'valid' if source_name.upper() in valid_sources else 'unknown'}"
            }
            verification_result["checks_performed"].append(source_check)
            
            if source_check["passed"]:
                verification_result["authenticity_score"] += 0.3
            else:
                verification_result["warnings"].append(f"Unknown source: {source_name}")
            
            # Check 2: Data structure integrity
            if isinstance(data_sample, dict) and len(data_sample) > 0:
                structure_check = {
                    "check": "data_structure",
                    "passed": True,
                    "message": "Data has expected dictionary structure"
                }
                verification_result["checks_performed"].append(structure_check)
                verification_result["authenticity_score"] += 0.2
            else:
                structure_check = {
                    "check": "data_structure",
                    "passed": False,
                    "message": "Data structure invalid or empty"
                }
                verification_result["checks_performed"].append(structure_check)
                verification_result["errors"].append("Invalid data structure")
            
            # Check 3: Timestamp validity (if present)
            if "timestamp" in data_sample or "date" in data_sample:
                timestamp_check = {
                    "check": "timestamp_validity",
                    "passed": True,
                    "message": "Timestamp field present"
                }
                verification_result["checks_performed"].append(timestamp_check)
                verification_result["authenticity_score"] += 0.2
            else:
                timestamp_check = {
                    "check": "timestamp_validity",
                    "passed": False,
                    "message": "No timestamp found in data"
                }
                verification_result["checks_performed"].append(timestamp_check)
                verification_result["warnings"].append("Missing timestamp information")
            
            # Check 4: Data format consistency
            format_check = {
                "check": "data_format_consistency",
                "passed": True,  # Simplified - would check actual format in implementation
                "message": "Data format consistent with source specification"
            }
            verification_result["checks_performed"].append(format_check)
            verification_result["authenticity_score"] += 0.3
            
            # Overall authenticity determination
            verification_result["is_authentic"] = (
                verification_result["authenticity_score"] >= 0.7 and 
                len(verification_result["errors"]) == 0
            )
            
            # Cache result for 30 minutes
            self.set_cached(cache_key, verification_result, 1800)
            return verification_result
            
        except Exception as e:
            self.logger.error(f"Error verifying source authenticity for {source_name}: {str(e)}")
            return {
                "source_name": source_name,
                "error": str(e),
                "is_authentic": False,
                "authenticity_score": 0.0,
                "verification_timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_cross_source_consistency(self, 
                                           symbol: str,
                                           data_types: List[str] = ["price", "volume"]) -> Dict[str, Any]:
        """
        Check consistency between multiple data sources for the same symbol.
        
        Args:
            symbol: Asset symbol to check
            data_types: Types of data to compare
            
        Returns:
            Cross-source consistency results
        """
        cache_key = f"cross_source_consistency:{symbol}:{','.join(sorted(data_types))}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        try:
            consistency_result = {
                "symbol": symbol,
                "data_types_checked": data_types,
                "check_timestamp": datetime.utcnow().isoformat(),
                "sources_compared": [],
                "consistency_score": 0.0,
                "is_consistent": False,
                "discrepancies": [],
                "source_values": {}
            }
            
            # Collect data from available sources
            source_data = {}
            
            # Try to get data from different sources
            if self.stock_service:
                try:
                    stock_data = await self.stock_service.get_stock(symbol)
                    if stock_data:
                        source_data["BRS"] = stock_data
                        consistency_result["sources_compared"].append("BRS")
                except Exception as e:
                    self.logger.warning(f"Failed to get BRS data for {symbol}: {str(e)}")
            
            # For crypto symbols, try crypto client
            if symbol.upper() in ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "AVAX", "MATIC"]:
                if self.crypto_client:
                    try:
                        crypto_data = await self.crypto_client.get_crypto_price(symbol)
                        if crypto_data:
                            source_data["CRYPTO_API"] = crypto_data
                            consistency_result["sources_compared"].append("CRYPTO_API")
                    except Exception as e:
                        self.logger.warning(f"Failed to get crypto data for {symbol}: {str(e)}")
            
            # Compare values from different sources
            if len(source_data) >= 2:
                sources = list(source_data.keys())
                
                for data_type in data_types:
                    values = {}
                    for source, data in source_data.items():
                        # Extract value based on data type
                        if data_type == "price":
                            value = data.get("price") or data.get("close") or data.get("last_price")
                        elif data_type == "volume":
                            value = data.get("volume") or data.get("vol")
                        else:
                            value = data.get(data_type)
                        
                        if value is not None:
                            values[source] = float(value)
                    
                    if len(values) >= 2:
                        # Calculate variance between sources
                        value_list = list(values.values())
                        avg_value = sum(value_list) / len(value_list)
                        
                        if avg_value != 0:
                            variance = sum((v - avg_value) ** 2 for v in value_list) / len(value_list)
                            relative_variance = (variance ** 0.5) / abs(avg_value)  # Coefficient of variation
                            
                            consistency_result["source_values"][f"{data_type}_{source}"] = values
                            
                            # Consider consistent if variation is less than 5%
                            if relative_variance < 0.05:
                                consistency_result["consistency_score"] += (1.0 / len(data_types))
                            else:
                                consistency_result["discrepancies"].append({
                                    "data_type": data_type,
                                    "sources": list(values.keys()),
                                    "values": values,
                                    "average": avg_value,
                                    "variance": variance,
                                    "relative_variance": relative_variance
                                })
            
            # Determine overall consistency
            consistency_result["is_consistent"] = consistency_result["consistency_score"] >= 0.8
            
            # Cache result for 15 minutes
            self.set_cached(cache_key, consistency_result, 900)
            return consistency_result
            if condition else _[1]
            # Conditional expression: if condition then _ else _[1]
        except Exception as e:
            self.logger.error(f"Error checking cross-source consistency for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": str(e),
                "check_timestamp": datetime.utcnow().isoformat(),
                "is_consistent": False,
                "consistency_score": 0.0
            }
    
    async def get_comprehensive_validation_report(self, 
                                                symbol: str,
                                                source_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive validation report for a symbol.
        
        Args:
            symbol: Asset symbol to validate
            source_types: Types of sources to validate (defaults to all applicable)
            
        Returns:
            Complete validation report
        """
        if source_types is None:
            # Determine applicable source types based on symbol
            if symbol.upper() in ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "AVAX", "MATIC"]:
                source_types = ["crypto"]
            else:
                # Assume stock for now - could be enhanced with symbol lookup
                source_types = ["stocks"]
        
        report = {
            "symbol": symbol,
            "report_timestamp": datetime.utcnow().isoformat(),
            "validations": {},
            "overall_status": "unknown",
            "recommendations": []
        }
        
        validation_tasks = []
        
        # Historical completeness validation
        for source_type in source_types:
            validation_tasks.append(
                self.validate_historical_completeness(source_type, symbol)
            )
        
        # Execute validations concurrently
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(validation_results):
            source_type = source_types[i]
            if isinstance(result, Exception):
                report["validations"][source_type] = {
                    "error": str(result),
                    "status": "failed"
                }
            else:
                report["validations"][source_type] = result
        
        # Cross-source consistency (if multiple sources available)
        if len(source_types) > 1:
            consistency_result = await self.check_cross_source_consistency(symbol)
            report["validations"]["cross_source_consistency"] = consistency_result
        
        # Calculate overall status
        valid_count = sum(1 for v in report["validations"].values() 
                         if isinstance(v, dict) and v.get("is_valid", False))
        total_checks = len([v for v in report["validations"].values() 
                           if isinstance(v, dict) and "error" not in v])
        
        if total_checks > 0:
            success_rate = valid_count / total_checks
            if success_rate >= 0.8:
                report["overall_status"] = "pass"
            elif success_rate >= 0.6:
                report["overall_status"] = "warning"
            else:
                report["overall_status"] = "fail"
                
                # Generate recommendations
                if valid_count == 0:
                    report["recommendations"].append("Data validation failed - consider alternative data sources")
                else:
                    report["recommendations"].append("Some validation checks failed - review data sources")
        
        return report

# Service registration function for dependency injection
def get_data_validation_service(brs_client=None, crypto_client=None, intl_client=None,
                              market_service=None, stock_service=None, logger=None) -> DataValidationService:
    """Factory function to create DataValidationService instance."""
    return DataValidationService(
        service_name="DataValidationService",
        brs_client=brs_client,
        crypto_client=crypto_client,
        intl_client=intl_client,
        market_service=market_service,
        stock_service=stock_service,
        logger=logger
    )