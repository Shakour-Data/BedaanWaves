"""
Sector Filter Service - Tier 7 Specialized Service

Provides industry/sector filtering based on user selections.
Enables users to filter stocks by industry sectors and sub-sectors.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from app.services.core.base_service import BaseService
import logging

class SectorFilterService(BaseService):
    """
    Sector Filter Service.
    
    Handles:
    - Industry/sector filtering based on user preferences
    - Sector hierarchy navigation
    - ETF-based sector analysis
    - Industry index tracking
    """
    
    def __init__(self,
                 service_name: str = "SectorFilterService",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize sector filter service.
        
        Args:
            service_name: Service identifier
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        
        # Sector hierarchy (sector -> sub-sectors)
        self.sector_hierarchy = {
            "Technology": [
                "Software", "Hardware", "Semiconductors", 
                "IT Services", "Telecommunications"
            ],
            "Healthcare": [
                "Pharmaceuticals", "Biotechnology", "Medical Devices",
                "Healthcare Services", "Health Insurance"
            ],
            "Financial": [
                "Banks", "Insurance", "Investment Banking",
                "Real Estate", "Consumer Finance"
            ],
            "Energy": [
                "Oil & Gas", "Renewable Energy", "Coal",
                "Electric Utilities", "Oil & Gas Equipment"
            ],
            "Materials": [
                "Chemicals", "Metals & Mining", "Construction Materials",
                "Packaging", "Forest Products"
            ],
            "Industrials": [
                "Machinery", "Transportation", "Aerospace & Defense",
                "Construction", "Industrial Machinery"
            ],
            "Consumer Discretionary": [
                "Retail", "Automobiles", "Media & Entertainment",
                "Restaurants", "Leisure Products"
            ],
            "Consumer Staples": [
                "Food & Beverage", "Tobacco", "Household Products",
                "Personal Care", "Agriculture"
            ],
            "Utilities": [
                "Electric Utilities", "Gas Utilities", "Water Utilities",
                "Renewable Utilities", "Independent Power"
            ],
            "Real Estate": [
                "REITs", "Real Estate Management", "Real Estate Development"
            ],
            "Communication Services": [
                "Telecom Services", "Media & Entertainment",
                "Social Media", "Publishing"
            ]
        }
        
        # Industry ETFs by sector
        self.sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financial": "XLF",
            "Energy": "XLE",
            "Materials": "XLB",
            "Industrials": "XLI",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Communication Services": "XLC"
        }
        
        # Industry classification systems
        self.industry_classifications = {
            "GICS": {
                "1010": "Energy",
                "1020": "Materials",
                "1030": "Industrials",
                "1040": "Real Estate",
                "1050": "Consumer Discretionary",
                "1060": "Financials",
                "1070": "Health Care",
                "1080": "Information Technology",
                "1090": "Communication Services",
                "1100": "Utilities",
                "1110": "Consumer Staples"
            },
            "ICB": {
                "0500": "Technology",
                "1000": "Financials",
                "1500": "Manufacturing",
                "2000": "Utilities",
                "2500": "Chemicals",
                "3000": "Construction",
                "3500": "Real Estate",
                "4000": "Automobiles",
                "4500": "Capital Goods",
                "5000": "Media",
                "5500": "Retailing",
                "6000": "Pharmaceuticals",
                "6500": "Biotechnology",
                "7000": "Food & Beverage",
                "7500": "Personal Care",
                "8000": "Health Care",
                "8500": "Banks",
                "9000": "Insurance",
                "9500": "Real Estate"
            }
        }
    
    async def initialize(self) -> None:
        """Initialize sector filter service."""
        self.logger.info("Initializing SectorFilterService")
        self.logger.info("SectorFilterService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown sector filter service."""
        self.logger.info("SectorFilterService shutdown")
    
    async def get_available_sectors(self) -> List[str]:
        """
        Get list of available sectors.
        
        Returns:
            List of sector names
        """
        return list(self.sector_hierarchy.keys())
    
    async def get_sub_sectors(self, sector: str) -> List[str]:
        """
        Get sub-sectors for a given sector.
        
        Args:
            sector: Sector name
            
        Returns:
            List of sub-sector names
        """
        return self.sector_hierarchy.get(sector, [])
    
    async def get_sector_etf(self, sector: str) -> Optional[str]:
        """
        Get ETF ticker for a sector.
        
        Args:
            sector: Sector name
            
        Returns:
            ETF ticker symbol or None
        """
        return self.sector_etfs.get(sector)
    
    async def filter_assets_by_sector(self,
                                      assets: List[Dict[str, Any]],
                                      selected_sectors: List[str]) -> List[Dict[str, Any]]:
        """
        Filter assets by selected sectors.
        
        Args:
            assets: List of assets to filter
            selected_sectors: List of sector names to include
            
        Returns:
            Filtered list of assets
        """
        if not selected_sectors:
            return assets
        
        filtered = []
        selected_lower = [s.lower() for s in selected_sectors]
        
        for asset in assets:
            asset_sector = asset.get("sector", asset.get("industry", ""))
            asset_sub_sector = asset.get("sub_sector", asset.get("industry", ""))
            
            # Check direct sector match
            if asset_sector.lower() in selected_lower:
                filtered.append(asset)
                continue
            
            # Check if sub-sector belongs to selected sector
            for sector, sub_sectors in self.sector_hierarchy.items():
                if sector.lower() in selected_lower:
                    if asset_sub_sector in sub_sectors or asset_sector in sub_sectors:
                        filtered.append(asset)
                        break
        
        return filtered
    
    async def filter_assets_by_industry(self,
                                        assets: List[Dict[str, Any]],
                                        selected_industries: List[str]) -> List[Dict[str, Any]]:
        """
        Filter assets by selected industries.
        
        Args:
            assets: List of assets to filter
            selected_industries: List of industry names to include
            
        Returns:
            Filtered list of assets
        """
        if not selected_industries:
            return assets
        
        filtered = []
        selected_lower = [i.lower() for i in selected_industries]
        
        for asset in assets:
            asset_industry = asset.get("industry", asset.get("sector", ""))
            asset_sub_sector = asset.get("sub_sector", "")
            
            if asset_industry.lower() in selected_lower:
                filtered.append(asset)
            elif asset_sub_sector and asset_sub_sector.lower() in selected_lower:
                filtered.append(asset)
        
        return filtered
    
    async def get_sector_analysis(self,
                                  sector: str,
                                  assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get analysis for a specific sector.
        
        Args:
            sector: Sector name
            assets: List of all assets
            
        Returns:
            Sector analysis results
        """
        sector_assets = await self.filter_assets_by_sector(assets, [sector])
        
        if not sector_assets:
            return {
                "sector": sector,
                "total_assets": 0,
                "analysis": "No assets found in this sector"
            }
        
        # Calculate sector metrics
        total_value = sum(a.get("market_cap", 0) for a in sector_assets)
        total_volume = sum(a.get("volume", 0) for a in sector_assets)
        
        # Sub-sector distribution
        sub_sector_dist = {}
        for asset in sector_assets:
            sub = asset.get("sub_sector", "Other")
            sub_sector_dist[sub] = sub_sector_dist.get(sub, 0) + 1
        
        # Get ETF for sector
        etf = await self.get_sector_etf(sector)
        
        return {
            "sector": sector,
            "total_assets": len(sector_assets),
            "total_market_cap": total_value,
            "total_volume": total_volume,
            "sub_sector_distribution": sub_sector_dist,
            "etf_ticker": etf,
            "assets": sector_assets[:10],  # Top 10 assets
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_industry_index(self, industry: str) -> Optional[str]:
        """
        Get industry index ticker.
        
        Args:
            industry: Industry name
            
        Returns:
            Industry index ticker or None
        """
        # Map industries to indices
        industry_indices = {
            "Software": "IXSW",
            "Semiconductors": "SOXX",
            "Biotechnology": "IBB",
            "Pharmaceuticals": "IHE",
            "Banks": "KBE",
            "Insurance": "IAK",
            "Oil & Gas": "XOP",
            "Renewable Energy": "ICLN",
            "Real Estate": "IYR",
            "Retail": "IYC",
            "Automobiles": "CARZ",
            "Media & Entertainment": "IYW"
        }
        
        return industry_indices.get(industry)
    
    async def apply_user_sector_preferences(self,
                                           assets: List[Dict[str, Any]],
                                           user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply user sector/industry preferences to filter assets.
        
        Args:
            assets: List of assets to filter
            user_preferences: User's preference configuration
            
        Returns:
            Filtered assets based on user sector preferences
        """
        selected_sectors = user_preferences.get("sectors", [])
        selected_industries = user_preferences.get("industries", [])
        
        # Apply sector filter first
        filtered = await self.filter_assets_by_sector(assets, selected_sectors)
        
        # Then apply industry filter
        filtered = await self.filter_assets_by_industry(filtered, selected_industries)
        
        return filtered
    
    async def get_sector_performance(self,
                                     assets: List[Dict[str, Any]],
                                     selected_sectors: List[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for sectors.
        
        Args:
            assets: List of assets
            selected_sectors: Optional list of sectors to analyze
            
        Returns:
            Sector performance metrics
        """
        if selected_sectors is None:
            selected_sectors = await self.get_available_sectors()
        
        performance = {}
        
        for sector in selected_sectors:
            sector_assets = await self.filter_assets_by_sector(assets, [sector])
            
            if not sector_assets:
                performance[sector] = {
                    "total_assets": 0,
                    "avg_change": 0,
                    "total_market_cap": 0
                }
                continue
            
            changes = [a.get("change_percent", 0) for a in sector_assets if a.get("change_percent")]
            avg_change = sum(changes) / len(changes) if changes else 0
            total_cap = sum(a.get("market_cap", 0) for a in sector_assets)
            
            performance[sector] = {
                "total_assets": len(sector_assets),
                "avg_change": round(avg_change, 2),
                "total_market_cap": total_cap,
                "etf_ticker": await self.get_sector_etf(sector)
            }
        
        return performance

# Factory function for dependency injection
def get_sector_filter_service(logger=None) -> SectorFilterService:
    """Factory function to create SectorFilterService instance."""
    return SectorFilterService(
        service_name="SectorFilterService",
        logger=logger
    )