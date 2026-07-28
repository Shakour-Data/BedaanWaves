"""Database Configuration and Session Management"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator, Generator
import logging
import os

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base Model
Base = declarative_base()

# Settings
settings = get_settings()

# Create async engine for PostgreSQL
url = settings.DATABASE_URL
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
engine = create_async_engine(
    url,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database by running Alembic migrations."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully")


async def drop_db() -> None:
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")


async def close_db() -> None:
    """Close database connection"""
    await engine.dispose()
    logger.info("Database connection closed")
