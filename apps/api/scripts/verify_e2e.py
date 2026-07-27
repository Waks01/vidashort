import asyncio
import uuid
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.models import Base, User, Series, Episode, UserIdentity
from app.core.security import hash_password, create_access_token


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


async def seed():
    async with SessionLocal() as db:
        user = User(
            id=str(uuid.uuid4()),
            email="test@vidashort.app",
            name="Test User",
            role="viewer",
            coins=100,
        )
        db.add(user)
        await db.flush()

        identity = UserIdentity(
            id=str(uuid.uuid4()),
            user_id=str(user.id),
            provider="email",
            provider_user_id=user.email,
            password_hash=hash_password("password123"),
        )
        db.add(identity)

        series = Series(
            id=str(uuid.uuid4()),
            slug="breaking-bad",
            title="Breaking Bad",
            synopsis="A high school chemistry teacher turned methamphetamine manufacturer.",
            cover_url="https://image.tmdb.org/t/p/w500/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
            backdrop_url="",
            category="drama",
            language="en",
            source="tmdb",
            tmdb_id="1396",
            total_episodes=5,
            free_episodes=1,
            is_vip_only=False,
            rating=9.5,
            tags_list=["drama", "crime", "thriller"],
        )
        db.add(series)
        await db.flush()

        for i in range(1, 6):
            ep = Episode(
                id=str(uuid.uuid4()),
                series_id=str(series.id),
                number=i,
                title=f"Episode {i}",
                synopsis=f"Episode {i} synopsis",
                duration_s=1200,
                required_coins=25 if i > 1 else 0,
                is_free=(i == 1),
                thumbnail_url="https://image.tmdb.org/t/p/w500/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
            )
            db.add(ep)

        await db.commit()
        print("Seeded test user + Breaking Bad series with 5 episodes.")


async def test_endpoints():
    import urllib.request
    import json

    base = "http://localhost:8000"

    payload = json.dumps({"email": "test@vidashort.app", "password": "password123"}).encode()
    req = urllib.request.Request(f"{base}/v1/auth/signin", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        token = data["accessToken"]
        print(f"Signin OK, user: {data['user']['email']}, role: {data['user']['role']}")

    req = urllib.request.Request(f"{base}/v1/content/series", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"Series list: {len(data['items'])} series")

    req = urllib.request.Request(f"{base}/v1/content/featured", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"Featured: {len(data['items'])} items")

    req = urllib.request.Request(f"{base}/v1/coins/packs", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"Coin packs: {len(data['packs'])} packs")

    req = urllib.request.Request(f"{base}/v1/me", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"Me: {data['user']['email']}, coins: {data['wallet']['coins']}")

    print("All backend endpoints verified.")


async def main():
    await init_db()
    await seed()
    await test_endpoints()


if __name__ == "__main__":
    asyncio.run(main())
