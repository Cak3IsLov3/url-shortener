"""Database models."""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    """Timezone-aware UTC 'now' — avoids the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class ShortURL(SQLModel, table=True):
    """A single shortened URL entry."""

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=32)
    original_url: str
    created_at: datetime = Field(default_factory=_utcnow)

    clicks: list["Click"] = Relationship(back_populates="short_url")


class Click(SQLModel, table=True):
    """A single click / redirect event on a shortened URL."""

    id: Optional[int] = Field(default=None, primary_key=True)
    short_url_id: int = Field(foreign_key="shorturl.id", index=True)
    timestamp: datetime = Field(default_factory=_utcnow)
    referrer: Optional[str] = Field(default=None, max_length=2048)
    user_agent: Optional[str] = Field(default=None, max_length=1024)

    short_url: Optional[ShortURL] = Relationship(back_populates="clicks")
