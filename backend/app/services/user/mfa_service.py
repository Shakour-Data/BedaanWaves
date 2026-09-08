"""MFA Service - TOTP-based multi-factor authentication."""

import base64
import hashlib
import hmac
import secrets
from io import BytesIO
from typing import Optional

import pyotp
import qrcode
from qrcode import constants as qr_constants
from sqlalchemy import select, update

from app.db.base import async_session_maker
from app.models.models import User


class MFAManager:
    """TOTP-based Multi-Factor Authentication manager."""

    ISSUER_NAME = "BedaanWaves"
    ALGORITHM = "sha1"
    DIGITS = 6
    PERIOD = 30

    def __init__(self) -> None:
        self._totp_cache: dict[int, pyotp.TOTP] = {}

    def generate_secret(self, user_id: int) -> str:
        """Generate a new TOTP secret for a user."""
        secret = pyotp.random_base32()
        self._totp_cache[user_id] = pyotp.TOTP(
            secret,
            algorithm=self.ALGORITHM,
            digits=self.DIGITS,
            interval=self.PERIOD,
        )
        return secret

    def get_provisioning_uri(self, user_id: int, email: str, secret: str) -> str:
        """Generate the provisioning URI for QR code scanning."""
        totp = pyotp.TOTP(
            secret,
            algorithm=self.ALGORITHM,
            digits=self.DIGITS,
            interval=self.PERIOD,
        )
        return totp.provisioning_uri(name=email, issuer_name=self.ISSUER_NAME)

    def generate_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 data URI."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qr_constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def verify_code(self, user_id: int, code: str, secret: str) -> bool:
        """Verify a TOTP code with 1-step clock skew tolerance."""
        totp = pyotp.TOTP(
            secret,
            algorithm=self.ALGORITHM,
            digits=self.DIGITS,
            interval=self.PERIOD,
        )
        return totp.verify(code, valid_window=1)

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate one-time backup codes."""
        return [secrets.token_urlsafe(8).upper() for _ in range(count)]

    def verify_backup_code(self, code: str, backup_codes: list[str]) -> bool:
        """Verify a backup code (one-time use)."""
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        for stored in backup_codes:
            if hmac.compare_digest(
                hashlib.sha256(stored.encode("utf-8")).hexdigest(),
                code_hash,
            ):
                return True
        return False

    def is_mfa_enabled(self, user_id: int) -> bool:
        """Check if MFA is enabled for a user."""
        return self._totp_cache.get(user_id) is not None

    def clear_cache(self, user_id: int) -> None:
        """Clear cached TOTP secret."""
        self._totp_cache.pop(user_id, None)


async def get_user_mfa_secret(user_id: int) -> Optional[str]:
    """Fetch MFA secret from database."""
    from app.models.models import UserMFA
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserMFA).where(UserMFA.user_id == user_id, UserMFA.is_enabled.is_(True))
        )
        mfa = result.scalars().first()
        return mfa.secret if mfa else None


async def enable_mfa(user_id: int, secret: str, backup_codes: list[str]) -> None:
    """Enable MFA for a user."""
    from app.models.models import UserMFA
    async with async_session_maker() as session:
        existing = await session.execute(
            select(UserMFA).where(UserMFA.user_id == user_id)
        )
        mfa = existing.scalars().first()
        if mfa:
            mfa.secret = secret
            mfa.backup_codes = backup_codes
            mfa.is_enabled = True
        else:
            mfa = UserMFA(
                user_id=user_id,
                secret=secret,
                backup_codes=backup_codes,
                is_enabled=True,
            )
            session.add(mfa)
        await session.commit()


async def disable_mfa(user_id: int) -> None:
    """Disable MFA for a user."""
    from app.models.models import UserMFA
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserMFA).where(UserMFA.user_id == user_id)
        )
        mfa = result.scalars().first()
        if mfa:
            mfa.is_enabled = False
            await session.commit()