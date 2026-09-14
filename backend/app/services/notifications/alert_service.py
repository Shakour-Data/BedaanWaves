"""Alert Service

Minimal implementation of alert management against the simple Alert model.
The API contract in alerts.py is elaborate (nested conditions, delivery settings,
history entries), but the database schema is simple: one row per alert with
JSONB condition, threshold_value, threshold_direction, notification_channel.

This service bridges the gap by serializing the simple model into the response
shapes the router expects. It's not a full-featured alerting system — it's
enough to make the endpoints work without 500s.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import async_session_maker
from app.models.models import Alert, Asset

logger = logging.getLogger(__name__)


class AlertService:
    """Minimal alert CRUD against the Alert table."""

    async def create_alert(self, user_id: str, request: Any) -> Dict[str, Any]:
        """Create a new alert. Returns a dict matching AlertResponse shape."""
        try:
            # Extract the first symbol from the request (the DB model is per-asset)
            symbols = request.symbols if hasattr(request, "symbols") and request.symbols else []
            if not symbols:
                raise ValueError("At least one symbol is required")

            symbol = symbols[0]

            # Look up the asset
            async with async_session_maker() as session:
                asset_result = await session.execute(
                    select(Asset).where(Asset.symbol == symbol)
                )
                asset = asset_result.scalar_one_or_none()
                if not asset:
                    raise ValueError(f"Symbol {symbol} not found")

                # Extract condition details from the request
                condition = {}
                threshold_value = None
                threshold_direction = "above"

                if hasattr(request, "condition") and request.condition:
                    cond = request.condition
                    condition = {
                        "type": cond.type.value if hasattr(cond.type, "value") else str(cond.type),
                    }
                    if hasattr(cond, "price_threshold") and cond.price_threshold:
                        threshold_value = cond.price_threshold.value
                    elif hasattr(cond, "score_threshold") and cond.score_threshold:
                        threshold_value = cond.score_threshold.threshold
                        threshold_direction = cond.score_threshold.direction

                # Extract notification channel
                notification_channel = "in_app"
                if hasattr(request, "delivery") and request.delivery:
                    channels = request.delivery.channels
                    if channels:
                        notification_channel = channels[0].value if hasattr(channels[0], "value") else str(channels[0])

                alert = Alert(
                    user_id=UUID(user_id),
                    asset_id=asset.id,
                    alert_type=condition.get("type", "price_above"),
                    condition=condition,
                    threshold_value=threshold_value,
                    threshold_direction=threshold_direction,
                    notification_channel=notification_channel,
                    is_active=request.is_active if hasattr(request, "is_active") else True,
                )
                session.add(alert)
                await session.commit()
                await session.refresh(alert)

                return self._alert_to_response(alert, asset)

        except SQLAlchemyError as exc:
            logger.error("Database error creating alert: %s", exc)
            raise
        except Exception as exc:
            logger.error("Error creating alert: %s", exc)
            raise

    async def check_alert_immediately(self, alert_id: str) -> None:
        """Stub: check if an alert should trigger. No-op for now."""
        # This would normally fetch current data and evaluate the condition.
        # For now, it's a no-op stub to satisfy the router's background task.
        logger.debug("check_alert_immediately called for %s (no-op)", alert_id)

    async def list_alerts(
        self,
        user_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        alert_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> List[Dict[str, Any]]:
        """List alerts for a user with optional filtering."""
        try:
            async with async_session_maker() as session:
                query = select(Alert, Asset).join(Asset, Alert.asset_id == Asset.id)
                query = query.where(Alert.user_id == UUID(user_id))

                if status:
                    # Map status enum to is_active
                    if status == "active":
                        query = query.where(Alert.is_active.is_(True))
                    elif status in ("paused", "disabled"):
                        query = query.where(Alert.is_active.is_(False))

                if symbol:
                    query = query.where(Asset.symbol == symbol)

                if alert_type:
                    query = query.where(Alert.alert_type == alert_type)

                query = query.offset((page - 1) * per_page).limit(per_page)
                result = await session.execute(query)
                rows = result.all()

                return [self._alert_to_response(alert, asset) for alert, asset in rows]

        except SQLAlchemyError as exc:
            logger.error("Database error listing alerts: %s", exc)
            raise

    async def get_alert(self, alert_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single alert by ID."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Alert, Asset)
                    .join(Asset, Alert.asset_id == Asset.id)
                    .where(Alert.id == UUID(alert_id), Alert.user_id == UUID(user_id))
                )
                row = result.first()
                if not row:
                    return None
                alert, asset = row
                return self._alert_to_response(alert, asset)

        except SQLAlchemyError as exc:
            logger.error("Database error getting alert: %s", exc)
            raise

    async def update_alert(
        self, alert_id: str, user_id: str, request: Any
    ) -> Optional[Dict[str, Any]]:
        """Update an existing alert."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Alert, Asset)
                    .join(Asset, Alert.asset_id == Asset.id)
                    .where(Alert.id == UUID(alert_id), Alert.user_id == UUID(user_id))
                )
                row = result.first()
                if not row:
                    return None
                alert, asset = row

                # Update fields if provided
                if hasattr(request, "is_active") and request.is_active is not None:
                    alert.is_active = request.is_active

                if hasattr(request, "condition") and request.condition:
                    cond = request.condition
                    alert.condition = {
                        "type": cond.type.value if hasattr(cond.type, "value") else str(cond.type),
                    }
                    if hasattr(cond, "price_threshold") and cond.price_threshold:
                        alert.threshold_value = cond.price_threshold.value
                    elif hasattr(cond, "score_threshold") and cond.score_threshold:
                        alert.threshold_value = cond.score_threshold.threshold
                        alert.threshold_direction = cond.score_threshold.direction

                await session.commit()
                await session.refresh(alert)

                return self._alert_to_response(alert, asset)

        except SQLAlchemyError as exc:
            logger.error("Database error updating alert: %s", exc)
            raise

    async def delete_alert(self, alert_id: str, user_id: str) -> bool:
        """Delete an alert. Returns True if deleted, False if not found."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Alert).where(Alert.id == UUID(alert_id), Alert.user_id == UUID(user_id))
                )
                alert = result.scalar_one_or_none()
                if not alert:
                    return False

                await session.delete(alert)
                await session.commit()
                return True

        except SQLAlchemyError as exc:
            logger.error("Database error deleting alert: %s", exc)
            raise

    async def toggle_alert(self, alert_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle alert active status."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Alert, Asset)
                    .join(Asset, Alert.asset_id == Asset.id)
                    .where(Alert.id == UUID(alert_id), Alert.user_id == UUID(user_id))
                )
                row = result.first()
                if not row:
                    return None
                alert, asset = row

                alert.is_active = not alert.is_active
                await session.commit()
                await session.refresh(alert)

                return self._alert_to_response(alert, asset)

        except SQLAlchemyError as exc:
            logger.error("Database error toggling alert: %s", exc)
            raise

    async def get_alert_history(
        self,
        user_id: str,
        symbol: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Get history of triggered alerts. Returns a paginated response."""
        try:
            async with async_session_maker() as session:
                query = select(Alert, Asset).join(Asset, Alert.asset_id == Asset.id)
                query = query.where(Alert.user_id == UUID(user_id), Alert.triggered_at.isnot(None))

                if symbol:
                    query = query.where(Asset.symbol == symbol)
                if alert_type:
                    query = query.where(Alert.alert_type == alert_type)
                if start_date:
                    query = query.where(Alert.triggered_at >= start_date)
                if end_date:
                    query = query.where(Alert.triggered_at <= end_date)

                # Count total
                count_query = select(func.count()).select_from(query.subquery())
                total = (await session.execute(count_query)).scalar() or 0

                # Paginate
                query = query.order_by(Alert.triggered_at.desc()).offset((page - 1) * per_page).limit(per_page)
                result = await session.execute(query)
                rows = result.all()

                entries = []
                for alert, asset in rows:
                    entries.append({
                        "id": str(alert.id),
                        "alert_id": str(alert.id),
                        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
                        "symbol": asset.symbol,
                        "condition_type": alert.alert_type,
                        "threshold_value": float(alert.threshold_value) if alert.threshold_value else 0.0,
                        "actual_value": 0.0,  # Not stored in the simple model
                        "message": f"Alert triggered for {asset.symbol}",
                        "delivered_via": [alert.notification_channel or "in_app"],
                        "delivery_status": "success",
                    })

                return {
                    "status": "ok",
                    "count": len(entries),
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
                    "entries": entries,
                }

        except SQLAlchemyError as exc:
            logger.error("Database error getting alert history: %s", exc)
            raise

    async def create_alerts_bulk(
        self, user_id: str, alerts: List[Any]
    ) -> Dict[str, Any]:
        """Create multiple alerts in bulk. Returns a summary response."""
        created = []
        errors = []

        for i, alert_request in enumerate(alerts):
            try:
                alert = await self.create_alert(user_id, alert_request)
                created.append(alert)
            except Exception as exc:
                errors.append({"index": i, "error": str(exc)})

        return {
            "status": "ok",
            "created_count": len(created),
            "failed_count": len(errors),
            "alerts": created,
            "errors": errors,
        }

    async def get_user_alert_stats(self, user_id: str) -> Dict[str, Any]:
        """Get alert statistics for a user."""
        try:
            async with async_session_maker() as session:
                # Total alerts
                total = (
                    await session.execute(
                        select(func.count()).where(Alert.user_id == UUID(user_id))
                    )
                ).scalar() or 0

                # Active alerts
                active = (
                    await session.execute(
                        select(func.count()).where(
                            Alert.user_id == UUID(user_id), Alert.is_active.is_(True)
                        )
                    )
                ).scalar() or 0

                # Triggered alerts
                triggered = (
                    await session.execute(
                        select(func.count()).where(
                            Alert.user_id == UUID(user_id), Alert.triggered_at.isnot(None)
                        )
                    )
                ).scalar() or 0

                return {
                    "total_alerts": total,
                    "active_alerts": active,
                    "triggered_alerts": triggered,
                }

        except SQLAlchemyError as exc:
            logger.error("Database error getting alert stats: %s", exc)
            raise

    def _alert_to_response(self, alert: Alert, asset: Asset) -> Dict[str, Any]:
        """Serialize an Alert + Asset into the AlertResponse shape."""
        # Map is_active to a status string
        if alert.is_active:
            status = "active"
        elif alert.triggered_at:
            status = "triggered"
        else:
            status = "paused"

        return {
            "id": str(alert.id),
            "user_id": str(alert.user_id),
            "name": f"{alert.alert_type} alert for {asset.symbol}",
            "description": None,
            "symbols": [asset.symbol],
            "condition": alert.condition or {"type": alert.alert_type},
            "delivery": {
                "channels": [alert.notification_channel or "in_app"],
                "email_address": None,
                "webhook_url": None,
                "webhook_headers": None,
            },
            "status": status,
            "cooldown_minutes": 60,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "updated_at": alert.created_at.isoformat() if alert.created_at else None,
            "expires_at": None,
            "last_triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "trigger_count": alert.triggered_count or 0,
        }
