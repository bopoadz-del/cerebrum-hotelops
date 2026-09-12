"""SQLAlchemy engine — SQLite for offline pytest, Postgres+pgvector in compose."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from hotelops.settings import get_settings


class Base(DeclarativeBase):
    pass


_ENGINE: Engine | None = None
_SESSION: sessionmaker[Session] | None = None


def _sqlite_path(url: str) -> Path | None:
    prefix = "sqlite+pysqlite:///"
    if url.startswith(prefix):
        raw = url[len(prefix) :]
        if raw.startswith("./"):
            return Path(raw[2:])
        if raw not in {":memory:", ""}:
            return Path(raw)
    return None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        settings = get_settings()
        path = _sqlite_path(settings.database_url)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
        kwargs: dict = {"future": True}
        if settings.database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _ENGINE = create_engine(settings.database_url, **kwargs)
        if settings.database_url.startswith("sqlite"):

            @event.listens_for(_ENGINE, "connect")
            def _fk(dbapi_conn, _):  # noqa: ANN001
                dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return _ENGINE


def get_sessionmaker() -> sessionmaker[Session]:
    global _SESSION
    if _SESSION is None:
        _SESSION = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SESSION


def session_scope() -> Generator[Session, None, None]:
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    from hotelops import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def reset_engine() -> None:
    global _ENGINE, _SESSION
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION = None
