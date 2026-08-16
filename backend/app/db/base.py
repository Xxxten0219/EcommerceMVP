from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all future persistence models."""


def create_all_tables() -> None:
    from app.db.session import engine
    from app.models import analytics, communication, organization  # noqa: F401

    Base.metadata.create_all(bind=engine)
