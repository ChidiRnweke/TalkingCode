"""Database session management."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from talkingcode.models.orm import Base


def get_engine(database_url: str) -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(
        database_url,
        echo=False,
        future=True,
    )


def get_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session maker."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def get_session(
    database_url: str,
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session context."""
    engine = get_engine(database_url)
    session_maker = get_session_maker(engine)
    
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    await engine.dispose()


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
