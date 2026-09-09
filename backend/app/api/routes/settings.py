"""Settings and Preferences Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_route_user_id
from app.schemas.schemas import MarketPreferencesResponse, RecentSearchesResponse
from app.services.user.preference_service import preference_service

router = APIRouter(tags=["settings"])

RECENT_SEARCHES_KEY = "recent_searches"
DEFAULT_RECENT_LIMIT = 8


def _normalize_recents(values, limit=DEFAULT_RECENT_LIMIT):
    """Return a clean, case-insensitively de-duplicated, capped list of tickers."""
    if not isinstance(values, list):
        return []
    seen = set()
    out = []
    for v in values:
        if isinstance(v, str) and v.strip() and v.strip().upper() not in seen:
            seen.add(v.strip().upper())
            out.append(v.strip())
    return out[:limit]


@router.get("/market-preferences", response_model=MarketPreferencesResponse)
async def get_market_preferences(user_id: UUID = Depends(get_route_user_id)):
    """
    Get market configuration preferences for the user.
    If not set, returns default platform-wide configuration.
    """
    from app.core.utils import utc_now_iso
    pref = await preference_service.get_preference(user_id, "market_preferences")

    if pref:
        return MarketPreferencesResponse(
            status="success",
            preferences=pref.value,
            timestamp=utc_now_iso(),
        )
    return MarketPreferencesResponse(
        status="success",
        preferences={
            "us": {
                "indices": [
                    {"id": "spx", "name": "S&P 500", "desc": "Standard & Poor's 500"},
                    {"id": "nas", "name": "NASDAQ", "desc": "NASDAQ Composite"}
                ],
                "note": "Live data is fetched from external APIs. No static prices."
            }
        },
        timestamp=utc_now_iso(),
    )


@router.post("/market-preferences", status_code=status.HTTP_200_OK)
async def save_market_preferences(
    data: dict[str, Any],
    user_id: UUID = Depends(get_route_user_id)
):
    """Save user market preferences."""
    await preference_service.set_preference(user_id, "market_preferences", data)
    return {"status": "success", "message": "Preferences saved"}


@router.get("/countries", response_model=list[dict[str, str]])
async def get_countries():
    """Get list of supported countries/regions."""
    return [
        {"id": "us", "name": "USA", "flag": "🇺🇸", "region": "North America"},
        {"id": "eu", "name": "Europe", "flag": "🇪🇺", "region": "Europe"},
        {"id": "as", "name": "Asia", "flag": "🌏", "region": "Asia Pacific"}
    ]


class RecentSearchAdd(BaseModel):
    query: str = Field(..., min_length=1, max_length=50)
    limit: int = Field(DEFAULT_RECENT_LIMIT, ge=0, le=50)


@router.get("/recent-searches", response_model=RecentSearchesResponse)
async def get_recent_searches(user_id: UUID = Depends(get_route_user_id)):
    """Return the current user's most-recently-used search terms (most recent first)."""
    from app.core.utils import utc_now_iso
    pref = await preference_service.get_preference(user_id, RECENT_SEARCHES_KEY)
    recents = _normalize_recents(pref.value if pref else None)
    return RecentSearchesResponse(
        status="success",
        searches=recents,
        count=len(recents),
        timestamp=utc_now_iso(),
    )


@router.post("/recent-searches", response_model=dict[str, Any])
async def add_recent_search(
    payload: RecentSearchAdd,
    user_id: UUID = Depends(get_route_user_id),
):
    """Record a search term for the current user (most-recent first, de-duplicated)."""
    query = payload.query.strip().upper()
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query must not be empty")

    pref = await preference_service.get_preference(user_id, RECENT_SEARCHES_KEY)
    existing = _normalize_recents(pref.value if pref else None, limit=payload.limit)

    # Remove any case-insensitive duplicate, then prepend the new query.
    existing = [v for v in existing if v.upper() != query]
    existing.insert(0, query)
    existing = existing[: payload.limit]

    await preference_service.set_preference(user_id, RECENT_SEARCHES_KEY, existing)
    return {"status": "success", "recent_searches": existing}
