from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine with Postgres connection pool configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for verbose SQL logging in development
    future=True,
)

# Async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for SQLAlchemy ORM models
class Base(DeclarativeBase):
    pass


# Dependency to yield async database sessions to FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
