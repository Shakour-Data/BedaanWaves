"""Authorization Service (Tier 6: User Services)

Centralizes role/permission resolution and authorization helpers used both by
the global auth guard middleware and by per-route permission dependencies.
"""

from typing import Iterable, List, Set

from app.core.config import get_settings
from app.models.models import User

settings = get_settings()


class AuthorizationService:
    """Resolves the permission set granted to a user and validates access."""

    def get_permissions(self, user: User) -> Set[str]:
        """Return the full set of permissions granted to ``user``."""
        if getattr(user, "is_admin", False):
            return set(settings.ADMIN_PERMISSIONS)
        return set(settings.DEFAULT_USER_PERMISSIONS)

    def has_permission(self, user: User, permission: str) -> bool:
        """True when ``user`` holds ``permission`` (admins hold everything)."""
        if getattr(user, "is_admin", False):
            return True
        return permission in settings.DEFAULT_USER_PERMISSIONS

    def has_any_permission(self, user: User, permissions: Iterable[str]) -> bool:
        """True when ``user`` holds at least one of ``permissions``."""
        return any(self.has_permission(user, p) for p in permissions)

    def has_all_permissions(self, user: User, permissions: Iterable[str]) -> bool:
        """True when ``user`` holds every permission in ``permissions``."""
        return all(self.has_permission(user, p) for p in permissions)

    def is_admin(self, user: User) -> bool:
        """True when ``user`` is an administrator."""
        return bool(getattr(user, "is_admin", False))


authorization_service = AuthorizationService()
