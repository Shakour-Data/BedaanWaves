"""
Saga Orchestrator for Distributed Transactions

Implements the Saga pattern (Orchestration style) for multi-service transactions.
Coordinates compensation actions when a saga step fails.

Supported flows:
- OrderFlow: Create Order → Reserve Stock → Process Payment → Confirm Order
- TradeFlow: Lock Funds → Match Trade → Release Funds → Settle Trade
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class SagaState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class SagaStepStatus(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    name: str
    execute: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
    compensate: Callable[[dict[str, Any]], Awaitable[None]] | None = None
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class SagaInstance:
    saga_id: str
    saga_type: str
    state: SagaState = SagaState.PENDING
    steps: list[SagaStep] = field(default_factory=list)
    current_step_index: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error: str | None = None


class SagaOrchestrator:
    """
    Orchestrates distributed transactions using the Saga pattern.

    Each saga consists of a sequence of steps. Each step has:
    - execute: The forward action
    compensate: The rollback action (optional)

    If any step fails, the orchestrator runs compensation actions
    in reverse order for all previously completed steps.
    """

    def __init__(self, event_bus=None):
        self._sagas: dict[str, SagaInstance] = {}
        self._event_bus = event_bus
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger("saga.orchestrator")

    async def start_saga(
        self,
        saga_type: str,
        steps: list[SagaStep],
        initial_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Start a new saga instance.

        Args:
            saga_type: Type identifier for the saga
            steps: List of SagaStep definitions
            initial_data: Initial data payload for the saga

        Returns:
            Saga instance ID
        """
        saga_id = str(uuid4())
        instance = SagaInstance(
            saga_id=saga_id,
            saga_type=saga_type,
            steps=steps,
            data=initial_data or {},
        )
        async with self._lock:
            self._sagas[saga_id] = instance

        await self._publish_event(
            "SagaStarted",
            {
                "saga_id": saga_id,
                "saga_type": saga_type,
                "total_steps": len(steps),
            },
        )

        asyncio.create_task(self._execute_saga(instance))
        return saga_id

    async def _execute_saga(self, instance: SagaInstance) -> None:
        """Execute saga steps sequentially with compensation on failure."""
        instance.state = SagaState.RUNNING
        completed_steps: list[tuple[int, SagaStep]] = []

        try:
            for i, step in enumerate(instance.steps):
                instance.current_step_index = i
                step.status = SagaStepStatus.EXECUTING
                instance.updated_at = datetime.utcnow()

                await self._publish_event(
                    "SagaStepStarted",
                    {
                        "saga_id": instance.saga_id,
                        "step_index": i,
                        "step_name": step.name,
                    },
                )

                try:
                    step.result = await step.execute(instance.data)
                    step.status = SagaStepStatus.COMPLETED
                    completed_steps.append((i, step))
                    instance.data.update(step.result or {})

                    await self._publish_event(
                        "SagaStepCompleted",
                        {
                            "saga_id": instance.saga_id,
                            "step_index": i,
                            "step_name": step.name,
                            "result": step.result,
                        },
                    )
                except Exception as exc:
                    step.status = SagaStepStatus.FAILED
                    step.error = str(exc)
                    instance.error = str(exc)
                    instance.state = SagaState.FAILED

                    await self._publish_event(
                        "SagaStepFailed",
                        {
                            "saga_id": instance.saga_id,
                            "step_index": i,
                            "step_name": step.name,
                            "error": str(exc),
                        },
                    )

                    await self._compensate(instance, completed_steps)
                    return

            instance.state = SagaState.COMPLETED
            instance.updated_at = datetime.utcnow()

            await self._publish_event(
                "SagaCompleted",
                {
                    "saga_id": instance.saga_id,
                    "saga_type": instance.saga_type,
                    "final_data": instance.data,
                },
            )

        except Exception as exc:
            instance.state = SagaState.FAILED
            instance.error = str(exc)
            self._logger.error(f"Saga {instance.saga_id} execution failed: {exc}", exc_info=True)

            await self._publish_event(
                "SagaFailed",
                {
                    "saga_id": instance.saga_id,
                    "error": str(exc),
                },
            )

    async def _compensate(
        self,
        instance: SagaInstance,
        completed_steps: list[tuple[int, SagaStep]],
    ) -> None:
        """Run compensation actions in reverse order."""
        instance.state = SagaState.COMPENSATING
        instance.updated_at = datetime.utcnow()

        await self._publish_event(
            "SagaCompensationStarted",
            {
                "saga_id": instance.saga_id,
                "steps_to_compensate": len(completed_steps),
            },
        )

        for i, step in reversed(completed_steps):
            step.status = SagaStepStatus.COMPENSATING

            if step.compensate is None:
                self._logger.warning(
                    f"Step {step.name} has no compensation action, skipping"
                )
                step.status = SagaStepStatus.COMPENSATED
                continue

            try:
                await step.compensate(instance.data)
                step.status = SagaStepStatus.COMPENSATED

                await self._publish_event(
                    "SagaStepCompensated",
                    {
                        "saga_id": instance.saga_id,
                        "step_index": i,
                        "step_name": step.name,
                    },
                )
            except Exception as exc:
                self._logger.error(
                    f"Compensation failed for step {step.name}: {exc}", exc_info=True
                )
                step.status = SagaStepStatus.FAILED
                step.error = str(exc)

        instance.state = SagaState.COMPENSATED
        instance.updated_at = datetime.utcnow()

        await self._publish_event(
            "SagaCompensated",
            {
                "saga_id": instance.saga_id,
                "saga_type": instance.saga_type,
            },
        )

    async def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish a saga lifecycle event."""
        if self._event_bus is None:
            return
        try:
            from app.infrastructure.events.event_bus import Event

            event = Event(
                event_type=event_type,
                data=data,
                source="saga.orchestrator",
            )
            await self._event_bus.publish(event)
        except Exception as exc:
            self._logger.warning(f"Failed to publish saga event: {exc}")

    def get_saga(self, saga_id: str) -> SagaInstance | None:
        """Get saga instance by ID."""
        return self._sagas.get(saga_id)

    def get_saga_status(self, saga_id: str) -> dict[str, Any] | None:
        """Get detailed saga status."""
        instance = self._sagas.get(saga_id)
        if instance is None:
            return None

        return {
            "saga_id": instance.saga_id,
            "saga_type": instance.saga_type,
            "state": instance.state.value,
            "current_step_index": instance.current_step_index,
            "total_steps": len(instance.steps),
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                }
                for s in instance.steps
            ],
            "data": instance.data,
            "error": instance.error,
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat(),
        }


def create_order_saga_steps(
    order_service,
    payment_service,
    inventory_service,
    notification_service,
) -> list[SagaStep]:
    """
    Create saga steps for the order flow:
    Create Order → Reserve Stock → Process Payment → Confirm Order → Send Notification

    Compensation:
    Cancel Payment → Release Stock → Cancel Order
    """
    async def create_order(data: dict[str, Any]) -> dict[str, Any]:
        return await order_service.create_order(data)

    async def compensate_order(data: dict[str, Any]) -> None:
        await order_service.cancel_order(data.get("order_id"))

    async def reserve_stock(data: dict[str, Any]) -> dict[str, Any]:
        return await inventory_service.reserve_stock(data)

    async def compensate_stock(data: dict[str, Any]) -> None:
        await inventory_service.release_stock(data.get("order_id"))

    async def process_payment(data: dict[str, Any]) -> dict[str, Any]:
        return await payment_service.process_payment(data)

    async def compensate_payment(data: dict[str, Any]) -> None:
        await payment_service.refund_payment(data.get("payment_id"))

    async def confirm_order(data: dict[str, Any]) -> dict[str, Any]:
        return await order_service.confirm_order(data.get("order_id"))

    async def send_notification(data: dict[str, Any]) -> dict[str, Any]:
        return await notification_service.send_order_confirmation(data)

    return [
        SagaStep(name="create_order", execute=create_order, compensate=compensate_order),
        SagaStep(name="reserve_stock", execute=reserve_stock, compensate=compensate_stock),
        SagaStep(name="process_payment", execute=process_payment, compensate=compensate_payment),
        SagaStep(name="confirm_order", execute=confirm_order),
        SagaStep(name="send_notification", execute=send_notification),
    ]