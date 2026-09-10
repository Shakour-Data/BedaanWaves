"""Privacy & Data Subject Rights Routes (GDPR/CCPA compliance)

Provides:
- GET /api/v1/privacy/export - Export all user data (data portability)
- DELETE /api/v1/privacy/delete - Delete user account and all associated data (right to erasure)
- GET /api/v1/privacy/consent - Get user consent status
- PUT /api/v1/privacy/consent - Update user consent preferences
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_active_user
from app.db.base import async_session_maker
from app.models.models import (
    Alert,
    AuditLog,
    Notification,
    Portfolio,
    Position,
    User,
    UserMarketSetting,
    UserPreference,
    Watchlist,
    WatchlistItem,
)
from app.schemas.schemas import ConsentUpdate, PrivacyExportResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["privacy"])


@router.get("/export", response_model=PrivacyExportResponse)
async def export_user_data(current_user: User = Depends(get_current_active_user)):
    """Export all user data for GDPR data portability (Article 20)."""
    async with async_session_maker() as session:
        try:
            watchlists = await session.execute(
                select(Watchlist).where(Watchlist.user_id == current_user.id)
            )
            watchlist_rows = watchlists.scalars().all()

            portfolios = await session.execute(
                select(Portfolio).where(Portfolio.user_id == current_user.id)
            )
            portfolio_rows = portfolios.scalars().all()

            preferences = await session.execute(
                select(UserPreference).where(UserPreference.user_id == current_user.id)
            )
            preference_rows = preferences.scalars().all()

            notifications = await session.execute(
                select(Notification).where(Notification.user_id == current_user.id)
            )
            notification_rows = notifications.scalars().all()

            alerts = await session.execute(
                select(Alert).where(Alert.user_id == current_user.id)
            )
            alert_rows = alerts.scalars().all()

            market_settings = await session.execute(
                select(UserMarketSetting).where(UserMarketSetting.user_id == current_user.id)
            )
            market_setting_rows = market_settings.scalars().all()

            audit_logs = await session.execute(
                select(AuditLog).where(AuditLog.user_id == current_user.id)
            )
            audit_log_rows = audit_logs.scalars().all()

            return PrivacyExportResponse(
                exported_at=datetime.now(UTC).isoformat(),
                user={
                    "id": str(current_user.id),
                    "username": current_user.username,
                    "email": current_user.email,
                    "full_name": current_user.full_name,
                    "preferred_language": current_user.preferred_language,
                    "theme": current_user.theme,
                    "notifications_enabled": current_user.notifications_enabled,
                    "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                },
                watchlists=[
                    {
                        "id": str(w.id),
                        "name": w.name,
                        "description": w.description,
                        "is_default": w.is_default,
                        "created_at": w.created_at.isoformat() if w.created_at else None,
                    }
                    for w in watchlist_rows
                ],
                portfolios=[
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "portfolio_type": p.portfolio_type,
                        "base_currency": p.base_currency,
                        "is_public": p.is_public,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in portfolio_rows
                ],
                preferences=[
                    {"key": p.key, "value": p.value, "updated_at": p.updated_at.isoformat() if p.updated_at else None}
                    for p in preference_rows
                ],
                notifications=[
                    {
                        "id": str(n.id),
                        "type": n.type,
                        "title": n.title,
                        "channel": n.channel,
                        "read": n.read,
                        "created_at": n.created_at.isoformat() if n.created_at else None,
                    }
                    for n in notification_rows
                ],
                alerts=[
                    {
                        "id": str(a.id),
                        "alert_type": a.alert_type,
                        "condition": a.condition,
                        "is_active": a.is_active,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in alert_rows
                ],
                market_settings=[
                    {
                        "id": str(m.id),
                        "countries": m.countries,
                        "indices": m.indices,
                        "industries": m.industries,
                    }
                    for m in market_setting_rows
                ],
                audit_logs=[
                    {
                        "action": a.action,
                        "entity": a.entity,
                        "entity_id": a.entity_id,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in audit_log_rows
                ],
            )
        except Exception as exc:
            logger.error("Failed to export user data: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export user data",
            )


@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_user_data(current_user: User = Depends(get_current_active_user)):
    """Delete user account and all associated data (GDPR right to erasure, Article 17)."""
    async with async_session_maker() as session:
        try:
            watchlist_items = await session.execute(
                select(WatchlistItem).join(Watchlist).where(Watchlist.user_id == current_user.id)
            )
            for item in watchlist_items.scalars().all():
                await session.delete(item)

            watchlists = await session.execute(
                select(Watchlist).where(Watchlist.user_id == current_user.id)
            )
            for w in watchlists.scalars().all():
                await session.delete(w)

            positions = await session.execute(
                select(Position).join(Portfolio).where(Portfolio.user_id == current_user.id)
            )
            for p in positions.scalars().all():
                await session.delete(p)

            portfolios = await session.execute(
                select(Portfolio).where(Portfolio.user_id == current_user.id)
            )
            for p in portfolios.scalars().all():
                await session.delete(p)

            preferences = await session.execute(
                select(UserPreference).where(UserPreference.user_id == current_user.id)
            )
            for p in preferences.scalars().all():
                await session.delete(p)

            notifications = await session.execute(
                select(Notification).where(Notification.user_id == current_user.id)
            )
            for n in notifications.scalars().all():
                await session.delete(n)

            alerts = await session.execute(
                select(Alert).where(Alert.user_id == current_user.id)
            )
            for a in alerts.scalars().all():
                await session.delete(a)

            market_settings = await session.execute(
                select(UserMarketSetting).where(UserMarketSetting.user_id == current_user.id)
            )
            for m in market_settings.scalars().all():
                await session.delete(m)

            from app.models.models import RefreshToken
            refresh_tokens = await session.execute(
                select(RefreshToken).where(RefreshToken.user_id == current_user.id)
            )
            for rt in refresh_tokens.scalars().all():
                await session.delete(rt)

            from app.models.models import UserMFA
            mfa = await session.execute(
                select(UserMFA).where(UserMFA.user_id == current_user.id)
            )
            for m in mfa.scalars().all():
                await session.delete(m)

            await session.delete(current_user)
            await session.commit()
            return {"status": "success", "message": "User data deleted successfully"}
        except Exception as exc:
            await session.rollback()
            logger.error("Failed to delete user data: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user data",
            )


@router.get("/consent")
async def get_consent(current_user: User = Depends(get_current_active_user)):
    """Get user consent status for data processing."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserPreference).where(
                UserPreference.user_id == current_user.id,
                UserPreference.key == "consent_preferences",
            )
        )
        consent = result.scalars().first()
        return {
            "user_id": str(current_user.id),
            "consent": consent.value if consent else {
                "data_processing": True,
                "marketing": False,
                "analytics": True,
                "third_party_sharing": False,
            },
        }


@router.put("/consent")
async def update_consent(
    data: ConsentUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Update user consent preferences for data processing."""
    from app.services.user.preference_service import PreferenceService
    pref_service = PreferenceService()
    await pref_service.set_preference(
        current_user.id,
        "consent_preferences",
        data.consents,
    )
    return {"status": "success", "message": "Consent preferences updated"}
