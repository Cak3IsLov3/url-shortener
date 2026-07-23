"""Application configuration loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the URL shortener."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base URL used when returning the shortened link. In production this should
    # be your public domain, e.g. "https://sho.rt".
    base_url: str = "http://localhost:8000"

    # SQLAlchemy-compatible database URL. SQLite works out of the box.
    database_url: str = "sqlite:///./shortener.db"

    # Length of the generated short codes. Six characters over an alphabet of
    # 62 (a-z, A-Z, 0-9) gives ~56 billion combinations.
    code_length: int = 6

    # Max attempts to generate a unique code before giving up.
    code_generation_max_attempts: int = 10


settings = Settings()
