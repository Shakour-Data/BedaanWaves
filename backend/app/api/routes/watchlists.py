"""Watchlist Routes (Tier 6)"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.dependencies import get_route_user_id
from app.schemas.schemas import (
    WatchlistResponse,
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistItemCreate,
)
from app.services.user.watchlist_service import watchlist_service

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    data: WatchlistCreate,
    user_id: UUID = Depends(get_route_user_id),
):
    return await watchlist_service.create_watchlist(
        user_id=user_id,
        name=data.name,
        description=data.description,
        is_default=data.is_default,
    )


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlists(user_id: UUID = Depends(get_route_user_id)):
    return await watchlist_service.list_watchlists(user_id)


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_route_user_id),
):
    watchlist = await watchlist_service.get_watchlist(watchlist_id, user_id)
    if watchlist is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_200_OK)
async def delete_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_route_user_id),
):
    deleted = await watchlist_service.delete_watchlist(watchlist_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"status": "success", "id": str(watchlist_id)}


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    watchlist_id: UUID,
    data: WatchlistItemCreate,
    user_id: UUID = Depends(get_route_user_id),
):
    item = await watchlist_service.add_item(
        watchlist_id=watchlist_id,
        user_id=user_id,
        asset_id=data.asset_id,
        note=data.note,
        alert_threshold_pct=data.alert_threshold_pct,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return item


@router.delete(
    "/{watchlist_id}/items/{item_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_item(
    watchlist_id: UUID,
    item_id: UUID,
    user_id: UUID = Depends(get_route_user_id),
):
    deleted = await watchlist_service.remove_item(watchlist_id, item_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"status": "success", "id": str(item_id)}
