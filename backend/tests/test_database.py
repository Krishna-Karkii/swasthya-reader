import os
import uuid

import pytest
from sqlalchemy import delete, func, select

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.database import create_database_engine
from app.db.models import ChatMessage, ChatSession, User


def test_database_persists_messages_and_cascades_user_deletion() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    message_id = uuid.uuid4()

    try:
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(User.__table__.insert().values(id=user_id))
            connection.execute(
                ChatSession.__table__.insert().values(id=session_id, user_id=user_id, title="Test")
            )
            connection.execute(
                ChatMessage.__table__.insert().values(
                    id=message_id,
                    session_id=session_id,
                    role="user",
                    content="Synthetic test message",
                )
            )

        with engine.connect() as connection:
            assert connection.scalar(
                select(func.count()).select_from(ChatMessage).where(ChatMessage.id == message_id)
            ) == 1
            connection.execute(delete(User).where(User.id == user_id))
            connection.commit()
            assert connection.scalar(
                select(func.count()).select_from(ChatSession).where(ChatSession.id == session_id)
            ) == 0
            assert connection.scalar(
                select(func.count()).select_from(ChatMessage).where(ChatMessage.id == message_id)
            ) == 0
    finally:
        engine.dispose()