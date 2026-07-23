"""Database engine setup and FastAPI session dependency."""
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# `check_same_thread=False` is required for SQLite when the same connection is
# used across threads (which FastAPI's TestClient and worker threads may do).
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Create all tables. Fine for MVP; use Alembic for real migrations."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
