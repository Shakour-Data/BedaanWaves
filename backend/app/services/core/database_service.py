"""
Database Service - Tier 1 Core Service

Manages database connections, session management, and transaction handling.
Integrates with SQLAlchemy for ORM functionality.
"""

import asyncio
from typing import Any, Dict, Optional, List, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .base_service import BaseService

from app.core.config import get_settings

settings = get_settings()


class DatabaseService(BaseService):
    """
    Database connection and session management service.
    
    Provides:
    - Connection pooling
    - Session management via context managers
    - Transaction handling
    - Connection health checks
    """
    
    def __init__(
        self,
        service_name: str = "DatabaseService",
        database_url: Optional[str] = None,
        async_mode: bool = True,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        echo: Optional[bool] = None,
    ):
        super().__init__(service_name)
        self.database_url = database_url or settings.DATABASE_URL
        self.async_mode = async_mode
        self.pool_size = pool_size if pool_size is not None else settings.DATABASE_POOL_SIZE
        self.max_overflow = max_overflow if max_overflow is not None else settings.DATABASE_MAX_OVERFLOW
        self.echo = echo if echo is not None else settings.DATABASE_ECHO
        
        self.engine = None
        self.session_factory = None
        self._connection_checks = 0
        self._session_counter = 0
        self._active_session_count = 0
    
    async def initialize(self) -> None:
        """Initialize database service with retry logic."""
        max_retries = 1
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if self.async_mode:
                    # Use asyncpg driver for async mode
                    if self.database_url.startswith("postgresql://"):
                        db_url = "postgresql+asyncpg://" + self.database_url[len("postgresql://"):]
                    else:
                        db_url = self.database_url
                    
                    self.engine = create_async_engine(
                        db_url,
                        echo=self.echo,
                        pool_size=self.pool_size,
                        max_overflow=self.max_overflow,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        connect_args={
                            "command_timeout": 5
                        }
                    )
                    self.session_factory = async_sessionmaker(
                        self.engine,
                        class_=AsyncSession,
                        expire_on_commit=False,
                    )
                else:
                    self.engine = create_engine(
                        self.database_url,
                        echo=self.echo,
                        poolclass=pool.QueuePool,
                        pool_size=self.pool_size,
                        max_overflow=self.max_overflow,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                    )
                    self.session_factory = sessionmaker(
                        self.engine,
                        expire_on_commit=False,
                    )
                
                # Test connection
                await self.health_check()
                health = await self.health_check()
                if health["status"] == "healthy":
                    self.logger.info(f"DatabaseService initialized with {self.database_url}")
                    return
                else:
                    raise Exception(f"Health check failed: {health.get('error')}")
            
            except Exception as e:
                self.logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    self.logger.error("All database connection attempts failed.")
                    self.engine = None
                    self.session_factory = None
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to the database."""
        self.logger.info("Attempting to reconnect to database...")
        try:
            await self.initialize()
            health = await self.health_check()
            return health["status"] == "healthy"
        except Exception as e:
            self.logger.error(f"Reconnection attempt failed: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown database service"""
        try:
            if self.engine:
                if self.async_mode:
                    await self.engine.dispose()
                else:
                    self.engine.dispose()
            
            self._active_session_count = 0
            self.logger.info("DatabaseService shutdown")
        except Exception as e:
            self.logger.error(f"Error during database shutdown: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session as async context manager.
        
        Usage:
            async with db_service.get_session() as session:
                result = await session.execute(query)
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self.session_factory()
        self._session_counter += 1
        self._active_session_count += 1
        session_id = self._session_counter
        
        try:
            yield session
        finally:
            self._active_session_count -= 1
            try:
                await session.close()
            except Exception as e:
                self.logger.warning(f"Error closing session {session_id}: {e}")
    
    async def execute(self, query: Any) -> Any:
        """
        Execute database query with automatic session management.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            Query result
        """
        async with self.get_session() as session:
            return await session.execute(query)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            self._connection_checks += 1
            
            if self.async_mode and self.engine:
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            elif self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            
            return {
                "service": self.service_name,
                "status": "healthy",
                "connection_checks": self._connection_checks,
                "active_sessions": self._active_session_count,
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e),
                "active_sessions": self._active_session_count,
            }
    
    def get_connection_url(self) -> str:
        """Get database connection URL (without password for security)"""
        url_parts = self.database_url.split('://')
        if len(url_parts) == 2:
            protocol = url_parts[0]
            rest = url_parts[1]
            
            if '@' in rest:
                creds, host = rest.rsplit('@', 1)
                user = creds.split(':')[0] if ':' in creds else creds
                return f"{protocol}://{user}:***@{host}"
        
        return self.database_url
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "service": self.service_name,
            "database_url": self.get_connection_url(),
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "active_sessions": self._active_session_count,
            "connection_checks": self._connection_checks,
            "async_mode": self.async_mode,
        }
