"""
Database engine and session management.

Provides an async SQLAlchemy engine backed by SQLite (via aiosqlite).
All database interactions in the application use the `get_db_session`
async context manager — never raw session objects.
"""
from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ── SQLAlchemy async engine ───────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False},
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base for ORM models ──────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All models in database_models.py must inherit from this class.
    """
    pass


async def initialize_database() -> None:
    """
    Create all database tables on application startup.

    This is idempotent — safe to call even if tables already exist.
    Import all ORM models before calling this to ensure they are
    registered with the metadata.
    """
    from app.models import database_models  # noqa: F401 — ensures models register
    from app.data_ingestion.cache_manager import CacheManager

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    # Initialize raw SQL cache table
    cache = CacheManager()
    await cache.initialize()

    logger.info("Database initialized successfully.")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Handles commit/rollback/close automatically. Inject via:
        session: AsyncSession = Depends(get_db_session)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
