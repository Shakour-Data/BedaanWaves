# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in BedaanWaves, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to **security@bedaanwaves.com** with:
- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes

### What to Expect

- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Regular Updates**: Every 5 business days
- **Resolution Timeline**: Based on severity (Critical: 7 days, High: 30 days, Medium: 90 days)

### Security Measures

BedaanWaves implements the following security controls:
- **Authentication**: JWT with RS256, refresh tokens, MFA support
- **Authorization**: RBAC with fine-grained permissions
- **Encryption**: AES-256 for data at rest, TLS 1.3 for data in transit
- **Monitoring**: Security audit logging, real-time monitoring
- **Scanning**: Automated dependency scanning (Snyk), SAST (Bandit), DAST (OWASP ZAP)
- **Incident Response**: 24/7 on-call security team with defined runbooks

### Security Audit Log

All sensitive operations are logged with:
- User ID and action performed
- Source IP address
- Timestamp (UTC)
- Result (success/failure)

Access the audit log via `/api/v1/security/audit-log` (admin only).

### Data Protection

- **Data Encryption**: Sensitive fields encrypted using AES-256 (Fernet)
- **Privacy Rights**: GDPR-compliant data export and deletion endpoints
- **Consent Management**: User consent preferences tracked and enforced
- **Data Retention**: Configurable retention policies for different data types

### Bug Bounty

We offer bug bounties for qualifying vulnerabilities:
- **Critical**: $500 - $2,000
- **High**: $200 - $500
- **Medium**: $50 - $200

Qualifying vulnerabilities include:
- Remote code execution
- Authentication bypass
- SQL injection
- Privilege escalation
- Sensitive data exposure

Non-qualifying issues:
- Self-XSS
- Clickjacking on non-sensitive pages
- Denial of service (DoS)
- Issues requiring physical access
- Issues requiring MITM without certificate pinning

### Security Contacts

- **Security Team**: security@bedaanwaves.com
- **PGP Key**: [Download from our website](https://bedaanwaves.com/pgp-key.asc)
- **Emergency**: +1-XXX-XXX-XXXX (for critical CVSS 9.0+)
