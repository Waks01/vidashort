from typing import Any

import httpx

from app.core.config import settings


async def search(query: str) -> list[dict[str, Any]]:
    if not settings.tmdb_api_key:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"api_key": settings.tmdb_api_key, "query": query},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])[:10]


async def details(tmdb_id: str) -> dict[str, Any] | None:
    if not settings.tmdb_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.themoviedb.org/3/tv/{tmdb_id}",
            params={"api_key": settings.tmdb_api_key},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def poster_url(tmdb_id: str, size: str = "w500") -> str | None:
    if not settings.tmdb_api_key:
        return None
    detail = await details(tmdb_id)
    if not detail or not detail.get("poster_path"):
        return None
    return f"https://image.tmdb.org/t/p/{size}{detail['poster_path']}"