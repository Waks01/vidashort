import time

from app.core.config import settings
from app.db.session import get_redis


async def check_rate_limit(key: str, limit: int, window_s: int) -> tuple[bool, int]:
    r = get_redis()
    now = time.time()
    window_start = now - window_s
    await r.zremrangebyscore(key, 0, window_start)
    count = await r.zcard(key)
    await r.zadd(key, {str(now): now})
    await r.expire(key, window_s)
    remaining = max(0, limit - int(count))
    allowed = int(count) < limit
    if not allowed:
        await r.zrem(key, str(now))
    return allowed, remaining


async def rate_limit(user_id: str | None, ip: str, endpoint: str, limit: int = 10, window_s: int = 60) -> None:
    from fastapi import HTTPException, status
    key_user = f"rl:{endpoint}:user:{user_id or 'anon'}"
    key_ip = f"rl:{endpoint}:ip:{ip}"
    for k in (key_user, key_ip):
        allowed, _ = await check_rate_limit(k, limit, window_s)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limited",
                headers={"Retry-After": str(window_s)},
            )


def _client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def rate_limit_dep(endpoint: str, limit: int, window_s: int):
    async def _check(request, user: dict | None = None) -> None:
        ip = _client_ip(request)
        uid = user.get("id") if user else None
        await rate_limit(uid, ip, endpoint, limit, window_s)
    return _check
