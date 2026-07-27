import asyncio
import secrets
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base import Base
from app.db.models import User, UserIdentity
from app.core.security import hash_password


async def create_admin(email: str, password: str, name: str = "Admin"):
    from app.core.config import settings
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()
    result = await session.execute(User.__table__.select().where(User.email == email))
    existing = result.fetchone()
    if existing:
        print(f"User {email} already exists")
        return
    user = User(
        id=__import__("uuid").uuid4(),
        email=email,
        name=name,
        role="admin",
    )
    identity = UserIdentity(
        id=__import__("uuid").uuid4(),
        user_id=user.id,
        provider="email",
        provider_user_id=email,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.add(identity)
    await session.commit()
    print(f"Admin user created: {email}")
    await session.close()
    await engine.dispose()


if __name__ == "__main__":
    email = input("Admin email: ")
    password = getpass("Admin password: ")
    asyncio.run(create_admin(email, password))