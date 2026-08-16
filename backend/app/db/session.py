from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings


def _ensure_sqlite_parent(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    path_value = database_url.removeprefix(prefix)
    if path_value == ":memory:":
        return

    Path(path_value).parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


settings = get_settings()
engine = create_database_engine(settings.database_url)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError:
        return False
