# ADR-007: Adopt TOTP-based Multi-Factor Authentication

## Status
Accepted

## Context
BedaanWaves handles sensitive financial data and user accounts. Current authentication relies solely on JWT tokens with password-based login. Industry standards and regulatory requirements demand multi-factor authentication for sensitive operations.

## Decision
Implement TOTP-based MFA using:
- `pyotp` library for TOTP code generation and verification
- QR code provisioning via `qrcode` library
- Backup codes for account recovery
- Database model `UserMFA` for storing MFA settings

## Consequences
- Positive: Enhanced security, compliance with industry standards, user confidence
- Negative: Additional login step for users, requires authenticator app
- Mitigation: Backup codes for account recovery, clear setup documentation

## Implementation
- Service: `app/services/user/mfa_service.py`
- Model: `UserMFA` in `app/models/models.py`
- API endpoints (planned):
  - `POST /api/v1/auth/mfa/setup`
  - `POST /api/v1/auth/mfa/verify`
  - `POST /api/v1/auth/mfa/disable`