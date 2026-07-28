"""Cryptocurrency Market Data Routes"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from app.services.data.crypto_api_client import CryptoApiClient
from app.services.crypto import CryptoPriceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market/crypto", tags=["crypto"])


async def _get_crypto_service() -> CryptoPriceService:
    client = CryptoApiClient()
    await client.initialize()
    service = CryptoPriceService(crypto_client=client)
    await service.initialize()
    return service


@router.get("/price/{symbol}", response_model=dict)
async def get_crypto_price(symbol: str, vs_currency: str = Query("usd")):
    """Get current price for a crypto asset (CoinGecko)."""
    service = await _get_crypto_service()
    try:
        data = await service.get_price(symbol, vs_currency)
        return {"status": "success", "symbol": symbol, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/ohlc/{symbol}", response_model=dict)
async def get_crypto_ohlc(symbol: str, days: int = Query(7, ge=1, le=365)):
    """Get OHLC candles for a crypto asset (CoinGecko)."""
    service = await _get_crypto_service()
    try:
        data = await service.get_ohlc(symbol, days)
        return {"status": "success", "symbol": symbol, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/ticker/{symbol}", response_model=dict)
async def get_binance_ticker(symbol: str = Query("BTCUSDT")):
    """Get 24h ticker from Binance."""
    client = CryptoApiClient()
    await client.initialize()
    try:
        data = await client.get_binance_ticker(symbol)
        return {"status": "success", "symbol": symbol, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if not client.session.closed:
            await client.shutdown()


@router.get("/depth/{symbol}", response_model=dict)
async def get_binance_depth(symbol: str = Query("BTCUSDT"), limit: int = Query(100, ge=1, le=5000)):
    """Get order book depth from Binance."""
    client = CryptoApiClient()
    await client.initialize()
    try:
        data = await client.get_binance_depth(symbol, limit)
        return {"status": "success", "symbol": symbol, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if not client.session.closed:
            await client.shutdown()


@router.get("/search", response_model=dict)
async def search_crypto(query: str = Query(..., min_length=1)):
    """Search crypto assets on CoinGecko."""
    client = CryptoApiClient()
    await client.initialize()
    try:
        data = await client.search(query)
        return {"status": "success", "query": query, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if not client.session.closed:
            await client.shutdown()
