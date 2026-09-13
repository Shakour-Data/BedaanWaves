# ADR-002: Split Database into Core, Market, and ML Databases

## Status
Accepted

## Context
A single PostgreSQL instance creates a single point of failure and makes scaling difficult. Different domains have different access patterns and scaling requirements.

## Decision
Split the monolithic database into three separate databases:
- `bedaanwaves_core`: Users, portfolios, settings
- `bedaanwaves_market`: Assets, prices, indicators, news
- `bedaanwaves_ml`: ML signals, models, coefficients

## Consequences
- Positive: Independent scaling, failure isolation, clearer domain boundaries
- Negative: Cross-database queries become harder, migration complexity
- Mitigation: Use event-driven data propagation where needed
