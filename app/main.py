"""FastAPI application entry point.

Endpoints:
    POST /shorten       -> create a short URL
    GET  /stats/{code}  -> click analytics for a short URL
    GET  /{code}        -> 302 redirect to the original URL (also logs a click)
"""
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config import settings
from app.database import create_db_and_tables, get_session
from app.models import Click, ShortURL
from app.schemas import (
    ReferrerCount,
    ShortenRequest,
    ShortenResponse,
    StatsResponse,
    UserAgentCount,
)
from app.shortener import generate_unique_code


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="URL Shortener",
    description=(
        "A minimal URL shortener with click analytics, built with FastAPI "
        "and SQLModel."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["meta"])
def root() -> dict:
    """Service metadata."""
    return {
        "name": "URL Shortener",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["urls"],
    summary="Create a short URL",
)
def shorten_url(
    payload: ShortenRequest,
    session: Session = Depends(get_session),
) -> ShortenResponse:
    code = generate_unique_code(
        session,
        length=settings.code_length,
        max_attempts=settings.code_generation_max_attempts,
    )
    short_url = ShortURL(code=code, original_url=str(payload.url))
    session.add(short_url)
    session.commit()
    session.refresh(short_url)

    return ShortenResponse(
        code=short_url.code,
        short_url=f"{settings.base_url.rstrip('/')}/{short_url.code}",
        original_url=short_url.original_url,
        created_at=short_url.created_at,
    )


# NOTE: /stats/{code} must be declared BEFORE /{code}, otherwise the catch-all
# /{code} route would match "stats" as a code first and never reach the stats
# handler.
@app.get(
    "/stats/{code}",
    response_model=StatsResponse,
    tags=["urls"],
    summary="Get click analytics for a short URL",
)
def get_stats(code: str, session: Session = Depends(get_session)) -> StatsResponse:
    short_url = session.exec(select(ShortURL).where(ShortURL.code == code)).first()
    if short_url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    clicks = session.exec(
        select(Click).where(Click.short_url_id == short_url.id)
    ).all()

    last_clicked_at = max((c.timestamp for c in clicks), default=None)

    referrer_counts = Counter(c.referrer for c in clicks if c.referrer)
    ua_counts = Counter(c.user_agent for c in clicks if c.user_agent)

    return StatsResponse(
        code=short_url.code,
        original_url=short_url.original_url,
        created_at=short_url.created_at,
        click_count=len(clicks),
        last_clicked_at=last_clicked_at,
        top_referrers=[
            ReferrerCount(value=v, count=n)
            for v, n in referrer_counts.most_common(5)
        ],
        top_user_agents=[
            UserAgentCount(value=v, count=n)
            for v, n in ua_counts.most_common(5)
        ],
    )


@app.get(
    "/{code}",
    tags=["urls"],
    summary="Redirect to the original URL",
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to the original URL."},
        404: {"description": "Short URL not found."},
    },
)
def redirect_to_original(
    code: str,
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    short_url = session.exec(select(ShortURL).where(ShortURL.code == code)).first()
    if short_url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    click = Click(
        short_url_id=short_url.id,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )
    session.add(click)
    session.commit()

    return RedirectResponse(
        url=short_url.original_url,
        status_code=status.HTTP_302_FOUND,
    )
