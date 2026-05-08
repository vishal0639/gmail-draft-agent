import sqlite3
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401 — register model metadata
from app.db.schema_compat import ensure_schema_compat

def _normalize_database_url(url: str) -> str:
    """Use psycopg v3 for bare postgresql:// URLs (Neon, Heroku, Docker, etc.)."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_s = get_settings()
_db_url = _normalize_database_url(_s.database_url)

connect_args: dict = {}
engine_kw: dict = {}
if _db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    engine_kw["pool_pre_ping"] = True

engine = create_engine(_db_url, connect_args=connect_args, **engine_kw)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def _sqlite_enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    """Create tables. For production use Alembic migrations."""
    Base.metadata.create_all(bind=engine)
    ensure_schema_compat(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
