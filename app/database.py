from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

class Settings(BaseSettings):
    """
    Configuration via environment variables.

    - DATABASE_URL: SQLAlchemy URL (PostgreSQL recommended)
      If omitted, falls back to SQLite for local dev.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "expense-tracker-backend"
    log_level: str = "INFO"
    database_url: str | None = None


settings = Settings()


def _default_sqlite_url() -> str:
    return "sqlite:///./local.db"


def get_database_url() -> str:
    return settings.database_url or _default_sqlite_url()


def create_db_engine() -> Engine:
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, future=True, connect_args=connect_args)


engine = create_db_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """
    Create tables for all registered SQLAlchemy models.
    Safe to call at startup (no-op if tables already exist).
    """

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy session per-request.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context-managed session for scripts/CLI usage.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
