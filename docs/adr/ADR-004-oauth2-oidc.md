# ADR-004: Adopt OAuth2/OIDC via Keycloak

## Status
Accepted

## Context
JWT alone does not provide SSO, token introspection, or centralized user management. Keycloak offers a production-ready identity provider.

## Decision
Integrate Keycloak as the identity provider using OpenID Connect.

## Consequences
- Positive: SSO, centralized user management, social login, fine-grained permissions
- Negative: Additional infrastructure, token exchange complexity
- Mitigation: Keep JWT as a fallback during migration
