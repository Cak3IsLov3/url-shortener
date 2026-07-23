"""Request and response schemas exposed by the API.

Kept separate from the SQLModel table models so the API contract does not
leak internal columns (e.g. primary keys) and vice versa.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    """Payload for POST /shorten."""

    url: HttpUrl = Field(..., description="The long URL to shorten.")


class ShortenResponse(BaseModel):
    """Response for POST /shorten."""

    code: str
    short_url: str
    original_url: str
    created_at: datetime


class ReferrerCount(BaseModel):
    value: str
    count: int


class UserAgentCount(BaseModel):
    value: str
    count: int


class StatsResponse(BaseModel):
    """Response for GET /stats/{code}."""

    code: str
    original_url: str
    created_at: datetime
    click_count: int
    last_clicked_at: Optional[datetime] = None
    top_referrers: list[ReferrerCount] = []
    top_user_agents: list[UserAgentCount] = []
