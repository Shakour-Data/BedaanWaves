# ADR-005: Implement Circuit Breaker and Bulkhead Patterns

## Status
Accepted

## Context
External API failures and traffic spikes can cascade through the system. Without resilience patterns, a single slow dependency can exhaust the entire application pool.

## Decision
Implement Circuit Breaker and Bulkhead patterns in the infrastructure layer.

## Consequences
- Positive: Fault isolation, graceful degradation, predictable failure modes
- Negative: Additional configuration complexity, tuning required
- Mitigation: Provide sensible defaults and per-tier bulkheads
