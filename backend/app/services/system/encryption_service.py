"""Encryption utilities for data-at-rest protection.

Uses Fernet (AES-256-CBC + HMAC-SHA256) for symmetric encryption of
sensitive fields stored in the database, such as data-source auth tokens.

The encryption key is read from the ``DATA_ENCRYPTION_KEY`` environment
variable.  In production this should be provisioned by a Secrets Manager
(HashiCorp Vault, AWS KMS, GCP Secret Manager, etc.) and never committed
to version control.
"""

import base64
import logging
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

_FERNET: Fernet | None = None


def _derive_key(master_secret: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_secret.encode()))


def get_fernet() -> Fernet | None:
    global _FERNET
    if _FERNET is not None:
        return _FERNET

    raw_key = os.environ.get("DATA_ENCRYPTION_KEY")
    if not raw_key:
        logger.warning(
            "DATA_ENCRYPTION_KEY is not set; field-level encryption is disabled. "
            "Set this environment variable to a 32-byte base64-encoded Fernet key."
        )
        return None

    try:
        _FERNET = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
    except Exception:
        salt = b"bedaanwaves_static_salt_v1"
        key = _derive_key(raw_key, salt)
        _FERNET = Fernet(key)

    return _FERNET


def encrypt_value(value: str) -> str:
    fernet = get_fernet()
    if fernet is None:
        raise RuntimeError(
            "DATA_ENCRYPTION_KEY is not configured; cannot encrypt value."
        )
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str | None:
    fernet = get_fernet()
    if fernet is None:
        raise RuntimeError(
            "DATA_ENCRYPTION_KEY is not configured; cannot decrypt value."
        )
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt value: invalid token or wrong key")
        return None
