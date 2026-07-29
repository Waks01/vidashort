"""Content tests — series list, series detail, episode stream + entitlement gate, favorites."""
import uuid
import pytest
from sqlalchemy import update

from app.db.models import Series, Episode
from tests.conftest import auth_headers, _current as _email_cap


async def _signup(client, email: str, password: str = "contentpass1", name: str = "ContentUser"):
    """Sign up + verify OTP, return the user id."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": password, "name": name,
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"]


async def _make_series(db_session, *, slug="test-drama", title="Test Drama",
                       free_episodes=3, total=5, is_published=True,
                       video_uid="cloudflare-uid-1"):
    series = Series(
        id=str(uuid.uuid4()),
        slug=slug,
        title=title,
        synopsis="Test synopsis",
        cover_url="https://cdn.example/cover.jpg",
        backdrop_url=None,
        category="drama",
        language="en",
        source="original",
        creator_id=None,
        is_published=is_published,
        free_episodes=free_episodes,
        total_episodes=total,
    )
    db_session.add(series)
    await db_session.flush()
    for n in range(1, total + 1):
        ep = Episode(
            id=str(uuid.uuid4()),
            series_id=series.id,
            number=n,
            title=f"Episode {n}",
            synopsis="",
            duration_s=120,
            video_uid=f"{video_uid}-{n}" if video_uid else None,
            video_ready=True,
            required_coins=25,
            is_free=(n <= free_episodes),
        )
        db_session.add(ep)
    await db_session.commit()
    return series


@pytest.mark.asyncio
async def test_list_series_returns_published_only(client, db_session):
    await _make_series(db_session=db_session, slug="pub", title="Published", is_published=True)
    await _make_series(db_session=db_session, slug="draft", title="Draft", is_published=False)

    resp = await client.get("/v1/content/series")
    assert resp.status_code == 200
    items = resp.json()["items"]
    slugs = [i["slug"] for i in items]
    assert "pub" in slugs
    assert "draft" not in slugs


@pytest.mark.asyncio
async def test_get_series_by_slug_returns_episodes(client, db_session):
    await _make_series(db_session=db_session, slug="ep-detail", title="EpDetail", total=4)

    resp = await client.get("/v1/content/series/ep-detail")
    assert resp.status_code == 200
    body = resp.json()
    assert body["series"]["slug"] == "ep-detail"
    assert len(body["episodes"]) == 4
    assert body["episodes"][0]["number"] == 1
    assert body["episodes"][0]["isFree"] is True  # within free_episodes=3
    assert body["episodes"][3]["isFree"] is False


@pytest.mark.asyncio
async def test_get_series_returns_404_for_unknown_slug(client):
    resp = await client.get("/v1/content/series/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


@pytest.mark.asyncio
async def test_stream_free_episode_allowed_without_coins(client, db_session):
    user_id = await _signup(client, "freebie@example.com", password="freebieword", name="Freebie")

    await _make_series(db_session=db_session, slug="freestream", total=3, free_episodes=1)
    resp = await client.get(
        "/v1/content/series/freestream/episodes/1/stream",
        headers=auth_headers(user_id),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["episodeId"]
    assert body["playbackUrl"].startswith("https://")


@pytest.mark.asyncio
async def test_stream_paid_episode_returns_403_when_no_coins_and_cap_hit(client, db_session):
    """With coins=0 AND ad_cap=0, decide() returns allowed=False → 403 paywall_required."""
    user_id = await _signup(client, "paid@example.com", password="paidpass1", name="Paida")

    await _make_series(db_session=db_session, slug="paidstream", total=5, free_episodes=2)

    # Pre-fill 100 ad impressions to saturate the cap
    import uuid as _uuid
    from sqlalchemy import insert as _insert
    from app.db.models import AdImpression as _AdImp
    for i in range(100):
        await db_session.execute(_insert(_AdImp).values(
            id=str(_uuid.uuid4()),
            user_id=user_id,
            ad_id=f"prefill-{i}",
            ad_network="appLovin",
            ad_type="rewarded",
            watched_s=15,
            completed=True,
            rewarded_coins=20,
        ))
    await db_session.commit()

    # Episode 4 is past the free window — no coins, no ads → 403
    resp = await client.get(
        "/v1/content/series/paidstream/episodes/4/stream",
        headers=auth_headers(user_id),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error"] == "paywall_required"


@pytest.mark.asyncio
async def test_favorite_then_unfavorite_roundtrip(client, db_session):
    series = await _make_series(db_session=db_session, slug="fav-me", total=1)
    user_id = await _signup(client, "favuser@example.com", password="favpass1", name="FavUser")
    headers = auth_headers(user_id)

    fav = await client.post(f"/v1/content/{series.id}/favorite", headers=headers)
    assert fav.status_code == 200
    assert fav.json() == {"ok": True}

    unfav = await client.post(f"/v1/content/{series.id}/unfavorite", headers=headers)
    assert unfav.status_code == 200
    assert unfav.json() == {"ok": True}


@pytest.mark.asyncio
async def test_list_series_filters_by_category(client, db_session):
    await _make_series(db_session=db_session, slug="cat-drama", title="Drama Cat")
    await _make_series(db_session=db_session, slug="cat-action", title="Action Cat")
    await db_session.execute(update(Series).where(Series.slug == "cat-action").values(category="action"))
    await db_session.commit()

    resp = await client.get("/v1/content/series", params={"category": "action"})
    items = resp.json()["items"]
    slugs = [i["slug"] for i in items]
    assert slugs == ["cat-action"]
