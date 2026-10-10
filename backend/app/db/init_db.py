from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.database import create_database_engine


def initialize_database() -> None:
    engine = create_database_engine()
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    initialize_database()