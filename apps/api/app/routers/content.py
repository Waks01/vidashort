from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.content import (
    EntitlementError,
    FeaturedResponse,
    FavoriteResponse,
    PaywallDecisionSchema,
    SeriesDetail,
    SeriesListResponse,
    StreamResponse,
)
from app.services import content as content_service

router = APIRouter()


@router.get("/series", response_model=SeriesListResponse)
async def list_series(
    cursor: str | None = Query(None),
    limit: int = Query(20, le=50),
    category: str | None = Query(None),
    source: str | None = Query(None),
    q: str | None = Query(None),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await content_service.list_series(db, cursor, limit, category, source, q, language)


@router.get("/series/{slug}", response_model=SeriesDetail)
async def get_series(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    return await content_service.get_series(db, slug)


@router.get("/series/{slug}/episodes/{n}/stream", response_model=StreamResponse, responses={403: {"model": EntitlementError}})
async def stream_episode(
    slug: str,
    n: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await content_service.stream_episode(db, user["id"], slug, n)


@router.post("/{series_id}/favorite", response_model=FavoriteResponse)
async def favorite(
    series_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await content_service.favorite(db, user["id"], series_id)
    return FavoriteResponse()


@router.post("/{series_id}/unfavorite", response_model=FavoriteResponse)
async def unfavorite(
    series_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await content_service.unfavorite(db, user["id"], series_id)
    return FavoriteResponse()


@router.get("/featured", response_model=FeaturedResponse)
async def featured(db: AsyncSession = Depends(get_db)):
    return await content_service.featured(db)