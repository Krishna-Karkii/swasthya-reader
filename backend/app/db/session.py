from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.database import create_database_engine


def get_database() -> Generator[Session, None, None]:
    engine = create_database_engine()
    try:
        with Session(engine) as database:
            yield database
    finally:
        engine.dispose()
