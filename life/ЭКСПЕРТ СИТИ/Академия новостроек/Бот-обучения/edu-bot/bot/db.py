"""Database engine and session factory (async SQLAlchemy)."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables. Call once at startup."""
    from bot.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
