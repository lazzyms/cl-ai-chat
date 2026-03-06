from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.settings import settings


def get_engine() -> Engine:
    """Return a SQLAlchemy engine from *settings.database_url*."""
    return create_engine(settings.database_url, pool_pre_ping=True)
