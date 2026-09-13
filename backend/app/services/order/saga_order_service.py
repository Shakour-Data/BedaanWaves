"""
Order Service - Saga-compatible order management

Provides order creation, confirmation, and cancellation
with proper saga integration for distributed transactions.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class OrderService:
    """Manages order lifecycle with saga support."""

    def __init__(self, order_repository=None, event_bus=None):
        self._repo = order_repository
        self._event_bus = event_bus
        self._logger = logging.getLogger("service.order")

    async def create_order(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new order."""
        order_id = str(uuid4())
        order = {
            "order_id": order_id,
            "user_id": data.get("user_id"),
            "items": data.get("items", []),
            "total_amount": data.get("total_amount", 0),
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
        }

        if self._repo:
            await self._repo.create(order)

        await self._publish_event("OrderCreated", order)
        self._logger.info(f"Order {order_id} created")

        return {"order_id": order_id, "status": "created"}

    async def confirm_order(self, order_id: str) -> dict[str, Any]:
        """Confirm an order after all saga steps complete."""
        if self._repo:
            await self._repo.update_status(order_id, "confirmed")

        await self._publish_event("OrderConfirmed", {"order_id": order_id})
        self._logger.info(f"Order {order_id} confirmed")

        return {"order_id": order_id, "status": "confirmed"}

    async def cancel_order(self, order_id: str | None) -> None:
        """Cancel an order (compensation action)."""
        if order_id and self._repo:
            await self._repo.update_status(order_id, "cancelled")

        await self._publish_event("OrderCancelled", {"order_id": order_id})
        self._logger.info(f"Order {order_id} cancelled")

    async def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish domain event."""
        if self._event_bus is None:
            return
        try:
            from app.infrastructure.events.event_bus import Event

            event = Event(event_type=event_type, data=data, source="order.service")
            await self._event_bus.publish(event)
        except Exception as exc:
            self._logger.warning(f"Failed to publish event: {exc}")


class PaymentService:
    """Manages payment processing with saga support."""

    def __init__(self, payment_gateway=None, event_bus=None):
        self._gateway = payment_gateway
        self._event_bus = event_bus
        self._logger = logging.getLogger("service.payment")

    async def process_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process payment for an order."""
        payment_id = str(uuid4())
        result = {
            "payment_id": payment_id,
            "order_id": data.get("order_id"),
            "amount": data.get("total_amount", 0),
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat(),
        }

        if self._gateway:
            try:
                gateway_result = await self._gateway.charge(data)
                result["gateway_response"] = gateway_result
            except Exception as exc:
                self._logger.error(f"Payment gateway failed: {exc}")
                raise

        await self._publish_event("PaymentProcessed", result)
        self._logger.info(f"Payment {payment_id} processed")

        return result

    async def refund_payment(self, payment_id: str | None) -> None:
        """Refund a payment (compensation action)."""
        if payment_id and self._gateway:
            try:
                await self._gateway.refund(payment_id)
                await self._publish_event("PaymentRefunded", {"payment_id": payment_id})
                self._logger.info(f"Payment {payment_id} refunded")
            except Exception as exc:
                self._logger.error(f"Refund failed for {payment_id}: {exc}")
                raise

    async def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        if self._event_bus is None:
            return
        try:
            from app.infrastructure.events.event_bus import Event

            event = Event(event_type=event_type, data=data, source="payment.service")
            await self._event_bus.publish(event)
        except Exception as exc:
            self._logger.warning(f"Failed to publish event: {exc}")


class InventoryService:
    """Manages stock reservation with saga support."""

    def __init__(self, inventory_repository=None, event_bus=None):
        self._repo = inventory_repository
        self._event_bus = event_bus
        self._logger = logging.getLogger("service.inventory")

    async def reserve_stock(self, data: dict[str, Any]) -> dict[str, Any]:
        """Reserve stock for an order."""
        order_id = data.get("order_id")
        items = data.get("items", [])

        reservation_id = str(uuid4())
        result = {
            "reservation_id": reservation_id,
            "order_id": order_id,
            "items": items,
            "status": "reserved",
            "reserved_at": datetime.utcnow().isoformat(),
        }

        if self._repo:
            await self._repo.reserve(items)

        await self._publish_event("StockReserved", result)
        self._logger.info(f"Stock reserved for order {order_id}")

        return result

    async def release_stock(self, order_id: str | None) -> None:
        """Release reserved stock (compensation action)."""
        if order_id and self._repo:
            await self._repo.release(order_id)
            await self._publish_event("StockReleased", {"order_id": order_id})
            self._logger.info(f"Stock released for order {order_id}")

    async def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        if self._event_bus is None:
            return
        try:
            from app.infrastructure.events.event_bus import Event

            event = Event(event_type=event_type, data=data, source="inventory.service")
            await self._event_bus.publish(event)
        except Exception as exc:
            self._logger.warning(f"Failed to publish event: {exc}")