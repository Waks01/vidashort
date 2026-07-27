import asyncio
import subprocess

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.db.base import Base


async def reset():
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database reset complete")


if __name__ == "__main__":
    asyncio.run(reset())