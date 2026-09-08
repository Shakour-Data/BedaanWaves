# ADR-001: Adopt Apache Kafka for Inter-Service Communication

## Status
Accepted

## Context
BedaanWaves requires asynchronous communication between services for data ingestion, analysis pipelines, and notification dispatch. The current synchronous REST-only approach creates tight coupling and limits scalability.

## Decision
Adopt Apache Kafka as the message broker for all asynchronous inter-service communication.

## Consequences
- Positive: Loose coupling, event replay capability, scalability, backpressure handling
- Negative: Operational complexity, learning curve, infrastructure overhead
- Mitigation: Start with InMemoryEventBus in development, switch to Kafka in production via config
