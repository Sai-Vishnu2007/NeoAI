"""
Database setup with async SQLAlchemy engine.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

# Database URL for SQLite with aiosqlite driver
DATABASE_URL = "sqlite+aiosqlite:///./agent.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for declarative models
Base = declarative_base()


async def get_db():
    """
    Dependency function to get database session.
    Yields an async session and ensures it's closed after use.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close the database engine.
    Should be called on application shutdown.
    """
    await engine.dispose()
