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
    
    # Default data matching the frontend's current hardcoded structure
    default_data = {
        "ir": {
            "indices": [
                {"id": "tepix", "name": "TEPIX", "desc": "Tehran Stock Exchange Index"},
                {"id": "tedpix", "name": "TEDPIX", "desc": "The Dow Iran"}
            ],
            "stocks": [
                {"id": "mav", "name": "Mave", "symbol": "MVE"},
                {"id": "dkd", "name": "Dekhoon Kala Dar", "symbol": "DKD"}
            ],
            "industries": [
                {"id": "energy", "name": "Energy", "change": "+2.5%"},
                {"id": "tech", "name": "Technology", "change": "+3.1%"}
            ],
            "crypto": [
                {"id": "btc", "name": "Bitcoin", "symbol": "BTC", "price": "$45,000", "change": "+2%"},
                {"id": "eth", "name": "Ethereum", "symbol": "ETH", "price": "$2,800", "change": "+1.5%"}
            ]
        },
        "us": {
            "indices": [
                {"id": "spx", "name": "S&P 500", "desc": "Standard & Poor's 500"},
                {"id": "nas", "name": "NASDAQ", "desc": "NASDAQ Composite"}
            ],
            "stocks": [
                {"id": "aapl", "name": "Apple", "symbol": "AAPL"},
                {"id": "msft", "name": "Microsoft", "symbol": "MSFT"}
            ],
            "industries": [
                {"id": "tech", "name": "Technology", "change": "+4.2%"},
                {"id": "health", "name": "Healthcare", "change": "+1.8%"}
            ],
            "crypto": [
                {"id": "btc", "name": "Bitcoin", "symbol": "BTC", "price": "$45,000", "change": "+2%"},
                {"id": "eth", "name": "Ethereum", "symbol": "ETH", "price": "$2,800", "change": "+2.1%"}
            ]
        }
    }
    
    if pref:
        return pref.value
    return default_data

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
        {"id": "ir", "name": "Iran", "flag": "🇮🇷", "region": "Middle East"},
        {"id": "us", "name": "USA", "flag": "🇺🇸", "region": "North America"},
        {"id": "eu", "name": "Europe", "flag": "🇪🇺", "region": "Europe"},
        {"id": "as", "name": "Asia", "flag": "🌏", "region": "Asia Pacific"},
        {"id": "crypto", "name": "Cryptocurrency", "flag": "₿", "region": "Digital"}
    ]
