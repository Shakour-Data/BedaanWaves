"""International Stock Market Data Routes"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from app.services.data.intl_api_client import IntlApiClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["intl"])


@router.get("/quote/{symbol}", response_model=dict)
async def get_intl_quote(symbol: str):
    """Get real-time quote for an international stock (stub)."""
    client = IntlApiClient()
    await client.initialize()
    try:
        data = await client.get_quote(symbol)
        return {"status": "success", "symbol": symbol, "data": data}
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=f"Intl quote pending vendor integration: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if client.session and not client.session.closed:
            await client.shutdown()


@router.get("/history/{symbol}", response_model=dict)
async def get_intl_history(symbol: str, interval: str = Query("1d")):
    """Get historical data for an international stock (stub)."""
    client = IntlApiClient()
    await client.initialize()
    try:
        data = await client.get_history(symbol, interval=interval)
        return {"status": "success", "symbol": symbol, "data": data}
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=f"Intl history pending vendor integration: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if client.session and not client.session.closed:
            await client.shutdown()


@router.get("/search", response_model=dict)
async def search_intl(query: str = Query(..., min_length=1)):
    """Search international stock symbols (stub)."""
    client = IntlApiClient()
    await client.initialize()
    try:
        data = await client.search(query)
        return {"status": "success", "query": query, "data": data}
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=f"Intl search pending vendor integration: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if client.session and not client.session.closed:
            await client.shutdown()
