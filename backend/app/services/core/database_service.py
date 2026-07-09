"""
Database Service - Tier 1 Core Service

Manages database connections, session management, and transaction handling.
Integrates with SQLAlchemy for ORM functionality.
"""

from typing import Any, Dict, Optional, List, AsyncGenerator
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .base_service import BaseService


class DatabaseService(BaseService):
    """
    Database connection and session management service.
    
    Provides:
    - Connection pooling
    - Session management
    - Transaction handling
    - Connection health checks
    """
    
    def __init__(
        self,
        service_name: str = "DatabaseService",
        database_url: str = "postgresql://localhost/bedaanwaves",
        async_mode: bool = True,
        pool_size: int = 20,
        max_overflow: int = 10,
        echo: bool = False,
    ):
        """
        Initialize database service.
        
        Args:
            service_name: Service identifier
            database_url: Database connection URL
            async_mode: Use async SQLAlchemy engine
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            echo: Log SQL statements
        """
        super().__init__(service_name)
        self.database_url = database_url
        self.async_mode = async_mode
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
        
        self.engine = None
        self.session_factory = None
        self._connection_checks = 0
        self._active_sessions: List[AsyncSession] = []
    
    async def initialize(self) -> None:
        """Initialize database service"""
        try:
            if self.async_mode:
                self.engine = create_async_engine(
                    self.database_url,
                    echo=self.echo,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,
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
            self.logger.info(f"DatabaseService initialized with {self.database_url}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown database service"""
        try:
            # Close all active sessions
            for session in self._active_sessions:
                await session.close()
            
            # Dispose engine
            if self.engine:
                if self.async_mode:
                    await self.engine.dispose()
                else:
                    self.engine.dispose()
            
            self.logger.info("DatabaseService shutdown")
        except Exception as e:
            self.logger.error(f"Error during database shutdown: {e}")
    
    async def get_session(self) -> AsyncSession:
        """
        Get database session.
        
        Returns:
            AsyncSession instance
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self.session_factory()
        self._active_sessions.append(session)
        return session
    
    async def execute(self, query: Any) -> Any:
        """
        Execute database query.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            Query result
        """
        session = await self.get_session()
        try:
            result = await session.execute(query)
            return result
        finally:
            await session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            self._connection_checks += 1
            
            # Try to get a connection from pool
            if self.async_mode and self.engine:
                async with self.engine.connect() as conn:
                    await conn.execute("SELECT 1")
            elif self.engine:
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
            
            return {
                "service": self.service_name,
                "status": "healthy",
                "connection_checks": self._connection_checks,
                "active_sessions": len(self._active_sessions),
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e),
            }
    
    async def clean_sessions(self) -> None:
        """Clean up closed sessions"""
        active_sessions = []
        for session in self._active_sessions:
            try:
                if session.is_active:
                    active_sessions.append(session)
                else:
                    await session.close()
            except:
                pass
        self._active_sessions = active_sessions
    
    def get_connection_url(self) -> str:
        """Get database connection URL (without password for security)"""
        # Parse URL and mask password
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
            "active_sessions": len(self._active_sessions),
            "connection_checks": self._connection_checks,
            "async_mode": self.async_mode,
        }
