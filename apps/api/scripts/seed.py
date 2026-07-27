import asyncio
import random
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base import Base
from app.db.models import User, Series, Episode
from app.core.security import hash_password


async def seed(db: AsyncSession):
    creator = User(
        id="00000000-0000-0000-0000-000000000001",
        email="creator@vidashort.app",
        name="LagosDrama",
        role="creator",
        coins=0,
        loyalty_coins=0,
        genres=["romance", "ceo"],
        onboarded=True,
        age_confirmed=True,
    )
    db.add(creator)
    series = Series(
        id="00000000-0000-0000-0000-000000000010",
        slug="the-ceos-forbidden-bride",
        title="The CEO's Forbidden Bride",
        synopsis="He married her to save his empire. He never expected to fall...",
        cover_url="https://cdn.vidashort.app/posters/ceo-bride.jpg",
        category="romance",
        source="original",
        creator_id=creator.id,
        total_episodes=3,
        free_episodes=1,
    )
    db.add(series)
    for i in range(1, 4):
        ep = Episode(
            id=f"00000000-0000-0000-0000-00000000001{i}",
            series_id=series.id,
            number=i,
            title=f"Episode {i}",
            synopsis=f"Synopsis for episode {i}",
            duration_s=90,
            is_free=(i == 1),
            required_coins=25,
        )
        db.add(ep)
    await db.commit()


async def main():
    from app.core.config import settings
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()
    await seed(session)
    await session.close()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())