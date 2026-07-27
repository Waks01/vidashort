from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import auth, me, content, entitlement, coins, ads, creator, admin, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title="vidashort-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(me.router, prefix="/v1/me", tags=["me"])
app.include_router(content.router, prefix="/v1/content", tags=["content"])
app.include_router(entitlement.router, prefix="/v1/entitlement", tags=["entitlement"])
app.include_router(coins.router, prefix="/v1/coins", tags=["coins"])
app.include_router(ads.router, prefix="/v1/ads", tags=["ads"])
app.include_router(creator.router, prefix="/v1/creator", tags=["creator"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["webhooks"])


@app.get("/health")
async def health():
    return {"ok": True}
