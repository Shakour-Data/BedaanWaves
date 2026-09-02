"""Settings and Preferences Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Dict, List, Any

from app.api.dependencies import get_route_user_id
from app.schemas.schemas import PreferenceResponse, PreferenceUpdate
from app.services.user.preference_service import preference_service

router = APIRouter(tags=["settings"])

@router.get("/market-preferences", response_model=Dict[str, Any])
async def get_market_preferences(user_id: UUID = Depends(get_route_user_id)):
    """
    Get market configuration preferences for the user.
    If not set, returns default platform-wide configuration.
    """
    pref = await preference_service.get_preference(user_id, "market_preferences")
    
    if pref:
        return pref.value
    return {
        "us": {
            "indices": [
                {"id": "spx", "name": "S&P 500", "desc": "Standard & Poor's 500"},
                {"id": "nas", "name": "NASDAQ", "desc": "NASDAQ Composite"}
            ],
            "note": "Live data is fetched from external APIs. No static prices."
        }
    }

@router.post("/market-preferences", status_code=status.HTTP_200_OK)
async def save_market_preferences(
    data: Dict[str, Any],
    user_id: UUID = Depends(get_route_user_id)
):
    """Save user market preferences."""
    await preference_service.set_preference(user_id, "market_preferences", data)
    return {"status": "success", "message": "Preferences saved"}

@router.get("/countries", response_model=List[Dict[str, str]])
async def get_countries():
    """Get list of supported countries/regions."""
    return [
        {"id": "us", "name": "USA", "flag": "🇺🇸", "region": "North America"},
        {"id": "eu", "name": "Europe", "flag": "🇪🇺", "region": "Europe"},
        {"id": "as", "name": "Asia", "flag": "🌏", "region": "Asia Pacific"}
    ]
