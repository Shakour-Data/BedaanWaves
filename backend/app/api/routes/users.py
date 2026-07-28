"""User Profile & Preferences Routes (Tier 6)"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.dependencies import get_route_user_id
from app.schemas.schemas import (
    UserResponse,
    UserProfileUpdate,
    PreferenceResponse,
    PreferenceUpdate,
)
from app.services.user.user_profile_service import user_profile_service
from app.services.user.preference_service import preference_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: UUID = Depends(get_route_user_id)):
    user = await user_profile_service.get_profile(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserProfileUpdate,
    user_id: UUID = Depends(get_route_user_id),
):
    user = await user_profile_service.update_profile(user_id, data.model_dump(exclude_unset=True))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/preferences", response_model=list[PreferenceResponse])
async def list_preferences(user_id: UUID = Depends(get_route_user_id)):
    prefs = await preference_service.list_preferences(user_id)
    return [PreferenceResponse(key=p.key, value=p.value) for p in prefs]


@router.get("/me/preferences/{key}", response_model=PreferenceResponse)
async def get_preference(key: str, user_id: UUID = Depends(get_route_user_id)):
    pref = await preference_service.get_preference(user_id, key)
    if pref is None:
        raise HTTPException(status_code=404, detail="Preference not found")
    return PreferenceResponse(key=pref.key, value=pref.value)


@router.put("/me/preferences/{key}", response_model=PreferenceResponse)
async def set_preference(
    key: str,
    data: PreferenceUpdate,
    user_id: UUID = Depends(get_route_user_id),
):
    pref = await preference_service.set_preference(user_id, key, data.value)
    return PreferenceResponse(key=pref.key, value=pref.value)


@router.delete("/me/preferences/{key}", status_code=status.HTTP_200_OK)
async def delete_preference(key: str, user_id: UUID = Depends(get_route_user_id)):
    deleted = await preference_service.delete_preference(user_id, key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"status": "success", "key": key}
