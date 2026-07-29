from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.db.session import get_db, get_redis
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


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError exceptions into the documented error envelope:
    { error: <code>, message: <detail> }. Status comes from the error class.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.detail},
    )


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Surface pending work as 501 with a recognizable code so clients (and
    the test suite) don't mistake it for an internal server error."""
    return JSONResponse(
        status_code=501,
        content={"error": "not_implemented", "message": str(exc) or "Endpoint not implemented"},
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
    """Liveness probe — pings the DB + Redis so Fly/Neon/Upstash wiring can be
    confirmed at a glance. Returns 200 only if both succeed; otherwise 503 with
    which subsystem failed (so the on-call knows where to look)."""
    db_status = "ok"
    redis_status = "ok"
    try:
        # One cheap roundtrip to confirm the connection pool works.
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            break
    except Exception:
        db_status = "down"

    try:
        await get_redis().ping()
    except Exception:
        redis_status = "down"

    body = {"ok": db_status == "ok" and redis_status == "ok", "db": db_status, "redis": redis_status}
    code = status.HTTP_200_OK if body["ok"] else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content=body)
