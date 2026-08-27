"""Tier 6: User Services

Services for user management:
- AuthService: Authentication and JWT
- AuthorizationService: Permission resolution
- UserProfileService: User profile management
- PreferenceService: User preferences
- NotificationService: Notification delivery
- WatchlistService: Watchlist management
- UserMarketSettingsService: User market settings
- UserCryptoSettingsService: User crypto settings
"""

from .auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_username,
    get_user_by_email,
    create_user,
    authenticate_user,
)
from .authorization_service import AuthorizationService
from .user_profile_service import UserProfileService
from .preference_service import PreferenceService
from .notification_service import NotificationService
from .watchlist_service import WatchlistService
from .user_market_settings_service import UserMarketSettingsService
from .user_crypto_settings_service import UserCryptoSettingsService

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_user_by_username",
    "get_user_by_email",
    "create_user",
    "authenticate_user",
    "AuthorizationService",
    "UserProfileService",
    "PreferenceService",
    "NotificationService",
    "WatchlistService",
    "UserMarketSettingsService",
    "UserCryptoSettingsService",
]
