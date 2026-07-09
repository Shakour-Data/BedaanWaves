"""
BrsApi.ir Integration Service

بسته‌ی سرویس‌ها برای ادغام API پلتفرم BrsApi.ir
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import get_settings
from decimal import Decimal

logger = logging.getLogger(__name__)

settings = get_settings()


class BrsApiClient:
    """BrsApi.ir Client - کلاینت برای ارتباط با API BrsApi.ir"""
    
    BASE_URL = "https://Api.BrsApi.ir/"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BRS API Client
        
        Args:
            api_key: API Key for BrsApi.ir (if None, use from settings)
        """
        self.api_key = api_key or settings.BRS_API_KEY or ""
        self.timeout = settings.BRS_API_TIMEOUT
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            follow_redirects=True,
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to BrsApi.ir
        
        Args:
            endpoint: API endpoint (e.g., "tsetmc-allsymbols")
            params: Query parameters
            
        Returns:
            Response data from API
        """
        if params is None:
            params = {}
        
        # Add API key to params
        params["key"] = self.api_key
        
        try:
            response = await self.client.get(
                endpoint,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"BrsApi request error: {str(e)}")
            raise
    
    # ==================== TSETMC (بورس) ====================
    
    async def get_all_symbols(self, symbol_type: Optional[int] = None) -> List[Dict]:
        """
        دریافت همه نمادهای بورسی
        
        API: tsetmc-allsymbols
        
        Args:
            symbol_type: نوع نماد (اختیاری)
                - None: همه انواع
                - 1: سهام عادی
                - 2: صندوق‌های ETF
                
        Returns:
            List of symbol dictionaries
        """
        params = {}
        if symbol_type:
            params["type"] = symbol_type
        
        response = await self._request("tsetmc-allsymbols", params)
        return response.get("data", [])
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات جامع نماد
        
        API: tsetmc-symbol
        
        Args:
            symbol: نام نماد (مثل "فولاد")
            
        Returns:
            Comprehensive symbol information
        """
        response = await self._request("tsetmc-symbol", {"symbol": symbol})
        return response.get("data", {})
    
    async def get_price_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        دریافت تاریخچه قیمت‌های روزانه
        
        API: tsetmc-history
        
        Args:
            symbol: نام نماد
            start_date: تاریخ شروع (YYYY-MM-DD)
            end_date: تاریخ پایان (YYYY-MM-DD)
            
        Returns:
            List of price history records
        """
        params = {"symbol": symbol}
        
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        
        response = await self._request("tsetmc-history", params)
        return response.get("data", [])
    
    async def get_candlestick(
        self,
        symbol: str,
        interval: str = "daily",
        limit: int = 100,
    ) -> List[Dict]:
        """
        دریافت کندل‌استیک (OHLCV)
        
        API: tsetmc-candlestick
        
        Args:
            symbol: نام نماد
            interval: بازه‌ی زمانی (daily, weekly, monthly)
            limit: تعداد کندل‌ها
            
        Returns:
            List of candlestick data
        """
        response = await self._request(
            "tsetmc-candlestick",
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            }
        )
        return response.get("data", [])
    
    async def get_market_indices(self) -> List[Dict]:
        """
        دریافت شاخص‌های بورس
        
        API: tsetmc-index
        
        Returns:
            List of market indices
        """
        response = await self._request("tsetmc-index")
        return response.get("data", [])
    
    async def get_etf_nav(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        دریافت NAV صندوق‌های ETF
        
        API: tsetmc-nav
        
        Args:
            symbol: نام صندوق (اختیاری - اگر None، همه صندوق‌ها)
            
        Returns:
            List of ETF NAV data
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        response = await self._request("tsetmc-nav", params)
        return response.get("data", [])
    
    async def get_shareholders(self, symbol: str) -> List[Dict]:
        """
        دریافت اطلاعات سهامداران
        
        API: tsetmc-shareholder
        
        Args:
            symbol: نام نماد
            
        Returns:
            List of shareholder information
        """
        response = await self._request(
            "tsetmc-shareholder",
            {"symbol": symbol}
        )
        return response.get("data", [])
    
    # ==================== IME (بورس کالا) ====================
    
    async def get_futures_contracts(self) -> List[Dict]:
        """
        دریافت قراردادهای آتی بورس کالا
        
        API: ime-futures
        
        Returns:
            List of futures contracts
        """
        response = await self._request("ime-futures")
        return response.get("data", [])
    
    # ==================== Commodity Price (طلا، ارز) ====================
    
    async def get_gold_currency(self) -> Dict[str, Any]:
        """
        دریافت قیمت طلا و ارز (رایگان)
        
        API: market-cgcc
        
        Returns:
            Gold and currency prices
        """
        response = await self._request("market-cgcc")
        return response.get("data", {})
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        دریافت نمای کلی بازار
        
        Returns:
            Market overview information
        """
        try:
            indices = await self.get_market_indices()
            symbols = await self.get_all_symbols()
            
            return {
                "total_symbols": len(symbols),
                "indices": indices,
                "last_update": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching market overview: {str(e)}")
            return {}


class BrsDataNormalizer:
    """
    تبدیل داده‌های BrsApi به فرمت یکپارچه‌ی سیستم
    """
    
    @staticmethod
    def normalize_symbol(brs_symbol: Dict[str, Any]) -> Dict[str, Any]:
        """
        تبدیل نماد BrsApi به فرمت سیستم
        
        Args:
            brs_symbol: Symbol data from BrsApi
            
        Returns:
            Normalized symbol data
        """
        return {
            "symbol": brs_symbol.get("symbol", ""),
            "name": brs_symbol.get("name", ""),
            "asset_class": "EQUITY",  # بورس = سهام عادی
            "market": "TSE",  # BrsApi = بورس تهران
            "sector": brs_symbol.get("sector"),
            "sub_sector": brs_symbol.get("subsector"),
            "country_code": "IR",
            "currency": "IRR",
        }
    
    @staticmethod
    def normalize_price_candle(brs_candle: Dict[str, Any]) -> Dict[str, Any]:
        """
        تبدیل کندل BrsApi به فرمت سیستم
        
        Args:
            brs_candle: Candlestick data from BrsApi
            
        Returns:
            Normalized candlestick data
        """
        return {
            "timestamp": brs_candle.get("date"),
            "timeframe": "1d",
            "open": Decimal(str(brs_candle.get("open", 0))),
            "high": Decimal(str(brs_candle.get("high", 0))),
            "low": Decimal(str(brs_candle.get("low", 0))),
            "close": Decimal(str(brs_candle.get("close", 0))),
            "volume": int(brs_candle.get("volume", 0)),
            "turnover": Decimal(str(brs_candle.get("value", 0))),
            "transactions": brs_candle.get("count"),
            "source": "BRS",
            "data_quality": "CONFIRMED",
        }
    
    @staticmethod
    def normalize_market_index(brs_index: Dict[str, Any]) -> Dict[str, Any]:
        """
        تبدیل شاخص بورس
        
        Args:
            brs_index: Index data from BrsApi
            
        Returns:
            Normalized index data
        """
        return {
            "symbol": brs_index.get("code", ""),
            "name": brs_index.get("name", ""),
            "current_value": Decimal(str(brs_index.get("value", 0))),
            "change": Decimal(str(brs_index.get("change", 0))),
            "timestamp": datetime.utcnow(),
            "market": "TSE",
        }
