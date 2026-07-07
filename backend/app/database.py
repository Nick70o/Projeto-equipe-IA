"""Database engine, session factory and declarative base.

SQLite is used for local/dev usage. The connection string comes from the
DATABASE_URL environment variable, so migrating to PostgreSQL later only
requires changing that variable (and the driver in requirements.txt) —
no application code should need to change.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread is only needed for SQLite; ignored by other drivers.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a managed database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
