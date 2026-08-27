"""Re-export canonical settings from app.core.config to avoid duplicate implementations."""
from app.core.config import get_settings

__all__ = ["get_settings"]