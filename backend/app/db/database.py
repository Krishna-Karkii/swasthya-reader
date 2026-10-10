import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine(database_url: str | None = None) -> Engine:
    resolved_url = database_url or os.environ.get("DATABASE_URL")
    if not resolved_url:
        raise RuntimeError("DATABASE_URL must be set")
    return create_engine(resolved_url, pool_pre_ping=True)