# ADR-003: Use Kong as API Gateway

## Status
Accepted

## Context
BedaanWaves needs a centralized entry point for security, rate limiting, and routing. Currently, FastAPI is exposed directly, which limits cross-cutting concerns.

## Decision
Deploy Kong as the API gateway in front of the FastAPI application.

## Consequences
- Positive: Centralized auth, rate limiting, logging, monitoring
- Negative: Additional infrastructure component, slight latency overhead
- Mitigation: Use Kong's declarative config for reproducible deployments
