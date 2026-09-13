"""
Resilience Testing for BedaanWaves Integration

Tests the system's ability to handle failures gracefully:
- Circuit breaker behavior
- Retry with backoff
- Bulkhead isolation
- Timeout handling
- Saga compensation
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState
from app.infrastructure.resilience.bulkhead import Bulkhead, BulkheadConfig
from app.infrastructure.resilience.retry_decorator import retry_with_backoff
from app.infrastructure.saga.saga_orchestrator import (
    SagaOrchestrator,
    SagaStep,
    SagaState,
)
from app.infrastructure.events.dlq_handler import DLQHandler, RetryHandler


class TestCircuitBreakerResilience:
    """Test Circuit Breaker pattern behavior."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker should open after failure threshold is reached."""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise ConnectionError("Service unavailable")

        # Fail 3 times to open the circuit
        for _ in range(3):
            try:
                await cb.call(failing_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Next call should fail immediately
        with pytest.raises(Exception):
            await cb.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Circuit breaker should recover after timeout."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.5)

        async def failing_func():
            raise ConnectionError("Service unavailable")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(2):
            try:
                await cb.call(failing_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.6)

        # Half-open state
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED


class TestBulkheadIsolation:
    """Test Bulkhead pattern for resource isolation."""

    @pytest.mark.asyncio
    async def test_bulkhead_limits_concurrent_calls(self):
        """Bulkhead should limit concurrent calls."""
        bulkhead = Bulkhead("test", BulkheadConfig(max_concurrent_calls=2))

        async def slow_func():
            await asyncio.sleep(0.5)
            return "done"

        # Start 2 concurrent calls (should succeed)
        task1 = asyncio.create_task(bulkhead.execute(slow_func))
        task2 = asyncio.create_task(bulkhead.execute(slow_func))

        await asyncio.sleep(0.1)

        # 3rd call should be rejected
        with pytest.raises(RuntimeError, match="saturated"):
            await bulkhead.execute(slow_func)

        await asyncio.gather(task1, task2)

    @pytest.mark.asyncio
    async def test_bulkhead_timeout(self):
        """Bulkhead should timeout long-running calls."""
        bulkhead = Bulkhead("test", BulkheadConfig(timeout=0.1))

        async def slow_func():
            await asyncio.sleep(1)
            return "done"

        with pytest.raises(TimeoutError):
            await bulkhead.execute(slow_func)


class TestRetryWithBackoff:
    """Test retry with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Retry should succeed after transient failures."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, jitter=False)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausts_max_retries(self):
        """Retry should fail after max retries."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01, jitter=False)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always failing")

        with pytest.raises(ConnectionError):
            await always_failing()

        assert call_count == 3  # Initial + 2 retries


class TestSagaCompensation:
    """Test Saga pattern compensation behavior."""

    @pytest.mark.asyncio
    async def test_saga_compensation_on_failure(self):
        """Saga should compensate completed steps when a later step fails."""
        saga = SagaOrchestrator()
        completed_steps = []

        async def step1_execute(data):
            completed_steps.append("step1")
            return {"step1_done": True}

        async def step1_compensate(data):
            completed_steps.append("step1_compensated")

        async def step2_execute(data):
            completed_steps.append("step2")
            return {"step2_done": True}

        async def step2_compensate(data):
            completed_steps.append("step2_compensated")

        async def step3_execute(data):
            raise RuntimeError("Step 3 failed")

        steps = [
            SagaStep(name="step1", execute=step1_execute, compensate=step1_compensate),
            SagaStep(name="step2", execute=step2_execute, compensate=step2_compensate),
            SagaStep(name="step3", execute=step3_execute),
        ]

        saga_id = await saga.start_saga("test", steps)
        await asyncio.sleep(0.1)  # Wait for saga to execute

        instance = saga.get_saga(saga_id)
        assert instance.state == SagaState.COMPENSATED
        assert "step1_compensated" in completed_steps
        assert "step2_compensated" in completed_steps


class TestDLQHandler:
    """Test Dead Letter Queue behavior."""

    @pytest.mark.asyncio
    async def test_retry_handler_exhaustion(self):
        """Retry handler should exhaust retries and raise."""
        handler = RetryHandler(max_retries=2, base_delay_ms=10, jitter=False)

        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await handler.execute_with_retry(always_fail)

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_dlq_topic_derivation(self):
        """DLQ topic name should be derived correctly."""
        handler = DLQHandler()
        assert handler._get_dlq_topic("bedaanwaves.orders.created") == "bedaanwaves.dlq.orders.created"
        assert handler._get_dlq_topic("bedaanwaves.payments.processed") == "bedaanwaves.dlq.payments.processed"


class TestIntegrationResilience:
    """End-to-end resilience tests."""

    @pytest.mark.asyncio
    async def test_external_service_failure_handling(self):
        """System should handle external service failures gracefully."""
        # Mock external payment gateway failure
        with patch("app.services.order.saga_order_service.PaymentService.process_payment") as mock_payment:
            mock_payment.side_effect = ConnectionError("Payment gateway timeout")

            from app.services.order.saga_order_service import (
                OrderService, PaymentService, InventoryService,
                create_order_saga_steps
            )

            order_service = OrderService()
            payment_service = PaymentService()
            inventory_service = InventoryService()

            steps = create_order_saga_steps(
                order_service=order_service,
                payment_service=payment_service,
                inventory_service=inventory_service,
                notification_service=MagicMock(),
            )

            saga = SagaOrchestrator()
            saga_id = await saga.start_saga("order", steps, {
                "user_id": "test-user",
                "items": [{"symbol": "AAPL", "quantity": 10}],
                "total_amount": 1755.00,
            })

            await asyncio.sleep(0.2)

            instance = saga.get_saga(saga_id)
            assert instance.state in [SagaState.FAILED, SagaState.COMPENSATED]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])