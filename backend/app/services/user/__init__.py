"""Tier 6: User Services

Services for user management:
- AuthService: Authentication and JWT
- AuthorizationService: Permission resolution
- UserProfileService: User profile management
- PreferenceService: User preferences
- NotificationService: Notification delivery
- WatchlistService: Watchlist management
- UserMarketSettingsService: User market settings
"""

from .auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_username,
    hash_password,
    verify_password,
)
from .authorization_service import AuthorizationService
from .notification_service import NotificationService
from .preference_service import PreferenceService
from .user_market_settings_service import UserMarketSettingsService
from .user_profile_service import UserProfileService
from .watchlist_service import WatchlistService

__all__ = [
    "AuthorizationService",
    "NotificationService",
    "PreferenceService",
    "UserMarketSettingsService",
    "UserProfileService",
    "WatchlistService",
    "authenticate_user",
    "create_access_token",
    "create_refresh_token",
    "create_user",
    "decode_token",
    "get_user_by_email",
    "get_user_by_username",
    "hash_password",
    "verify_password",
]
