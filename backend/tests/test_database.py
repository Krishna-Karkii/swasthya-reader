import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.database import create_database_engine
from app.db.models import ChatMessage, ChatSession, LabResult, Report, User
from app.db.queries import load_message_page, load_recent_messages, load_session_reports


def test_database_persists_messages_and_cascades_user_deletion() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    message_id = uuid.uuid4()
    report_id = uuid.uuid4()
    result_id = uuid.uuid4()

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
            connection.execute(
                Report.__table__.insert().values(
                    id=report_id,
                    session_id=session_id,
                    status="completed",
                    mime_type="image/png",
                    original_filename="synthetic.png",
                    extraction_json={"results": [{"test_name": "Glucose", "value": 99, "unit": "mg/dL"}]},
                )
            )
            connection.execute(
                LabResult.__table__.insert().values(
                    id=result_id,
                    report_id=report_id,
                    test_name_original="Glucose",
                    value_numeric=99,
                    unit="mg/dL",
                    status="unverified",
                )
            )

        with engine.connect() as connection:
            assert connection.scalar(
                select(func.count()).select_from(ChatMessage).where(ChatMessage.id == message_id)
            ) == 1
            assert connection.scalar(
                select(func.count()).select_from(LabResult).where(LabResult.id == result_id)
            ) == 1
            connection.execute(delete(User).where(User.id == user_id))
            connection.commit()
            assert connection.scalar(
                select(func.count()).select_from(ChatSession).where(ChatSession.id == session_id)
            ) == 0
            assert connection.scalar(
                select(func.count()).select_from(ChatMessage).where(ChatMessage.id == message_id)
            ) == 0
            assert connection.scalar(
                select(func.count()).select_from(Report).where(Report.id == report_id)
            ) == 0
            assert connection.scalar(
                select(func.count()).select_from(LabResult).where(LabResult.id == result_id)
            ) == 0
    finally:
        engine.dispose()


def test_database_rejects_invalid_report_and_result_status() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    report_id = uuid.uuid4()

    try:
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(User.__table__.insert().values(id=user_id))
            connection.execute(
                ChatSession.__table__.insert().values(id=session_id, user_id=user_id)
            )

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    Report.__table__.insert().values(
                        id=report_id,
                        session_id=session_id,
                        status="diagnosed",
                        mime_type="image/png",
                    )
                )

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    Report.__table__.insert().values(
                        id=report_id,
                        session_id=session_id,
                        status="uploaded",
                        mime_type="image/png",
                    )
                )
                connection.execute(
                    LabResult.__table__.insert().values(
                        report_id=report_id,
                        test_name_original="Glucose",
                        status="diagnosed",
                    )
                )
    finally:
        with engine.begin() as connection:
            connection.execute(delete(User).where(User.id == user_id))
        engine.dispose()


def test_recent_messages_are_bounded_ordered_and_owner_scoped() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    other_session_id = uuid.uuid4()
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    try:
        Base.metadata.create_all(engine)
        with Session(engine) as database:
            owner = User(id=owner_id)
            other_user = User(id=other_user_id)
            chat_session = ChatSession(id=session_id, user=owner)
            other_session = ChatSession(id=other_session_id, user=other_user)
            chat_session.messages = [
                ChatMessage(
                    role="user",
                    content=f"turn {index}",
                    created_at=start_time + timedelta(minutes=index),
                )
                for index in range(4)
            ]
            other_session.messages = [
                ChatMessage(role="user", content="different session", created_at=start_time)
            ]
            database.add_all([owner, other_user])
            database.commit()

            recent = load_recent_messages(
                database, user_id=owner_id, session_id=session_id, limit=2
            )
            assert [message.content for message in recent] == ["turn 2", "turn 3"]
            assert load_recent_messages(
                database, user_id=other_user_id, session_id=other_session_id
            )[0].content == "different session"
            assert "different session" not in [
                message.content
                for message in load_recent_messages(
                    database, user_id=owner_id, session_id=session_id, limit=20
                )
            ]
            assert load_recent_messages(
                database, user_id=other_user_id, session_id=session_id
            ) == []

            with pytest.raises(ValueError, match="limit must be between"):
                load_recent_messages(
                    database, user_id=owner_id, session_id=session_id, limit=21
                )

            database.delete(owner)
            database.delete(other_user)
            database.commit()
    finally:
        engine.dispose()


def test_message_pages_are_stable_and_owner_scoped() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    owner_id = uuid.uuid4()
    session_id = uuid.uuid4()
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    try:
        Base.metadata.create_all(engine)
        with Session(engine) as database:
            owner = User(id=owner_id)
            chat_session = ChatSession(id=session_id, user=owner)
            chat_session.messages = [
                ChatMessage(
                    id=uuid.UUID(int=index + 1),
                    role="user",
                    content=f"turn {index}",
                    created_at=start_time + timedelta(minutes=index // 2),
                )
                for index in range(5)
            ]
            database.add(owner)
            database.commit()

            newest_page = load_message_page(
                database, user_id=owner_id, session_id=session_id, limit=2
            )
            older_page = load_message_page(
                database,
                user_id=owner_id,
                session_id=session_id,
                limit=2,
                before=(newest_page[0].created_at, newest_page[0].id),
            )
            oldest_page = load_message_page(
                database,
                user_id=owner_id,
                session_id=session_id,
                limit=2,
                before=(older_page[0].created_at, older_page[0].id),
            )

            all_pages = newest_page + older_page + oldest_page
            assert [message.content for message in newest_page] == ["turn 3", "turn 4"]
            assert [message.content for message in older_page] == ["turn 1", "turn 2"]
            assert [message.content for message in oldest_page] == ["turn 0"]
            assert len({message.id for message in all_pages}) == 5
            assert load_message_page(
                database, user_id=uuid.uuid4(), session_id=session_id
            ) == []

            with pytest.raises(ValueError, match="limit must be between"):
                load_message_page(
                    database, user_id=owner_id, session_id=session_id, limit=51
                )

            database.delete(owner)
            database.commit()
    finally:
        engine.dispose()


def test_session_reports_are_newest_first_bounded_and_owner_scoped() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL test database")

    engine = create_database_engine(database_url)
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    other_session_id = uuid.uuid4()
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    try:
        Base.metadata.create_all(engine)
        with Session(engine) as database:
            owner = User(id=owner_id)
            other_user = User(id=other_user_id)
            chat_session = ChatSession(id=session_id, user=owner)
            other_session = ChatSession(id=other_session_id, user=other_user)
            chat_session.reports = [
                Report(
                    id=uuid.UUID(int=index + 1),
                    status="completed",
                    mime_type="image/png",
                    original_filename=f"synthetic-{index}.png",
                    created_at=start_time + timedelta(minutes=index // 2),
                )
                for index in range(4)
            ]
            other_session.reports = [
                Report(
                    status="completed",
                    mime_type="image/png",
                    original_filename="other-user.png",
                    created_at=start_time + timedelta(minutes=10),
                )
            ]
            database.add_all([owner, other_user])
            database.commit()

            reports = load_session_reports(
                database, user_id=owner_id, session_id=session_id, limit=2
            )
            assert [report.original_filename for report in reports] == [
                "synthetic-3.png",
                "synthetic-2.png",
            ]
            older_reports = load_session_reports(
                database,
                user_id=owner_id,
                session_id=session_id,
                limit=2,
                before=(reports[-1].created_at, reports[-1].id),
            )
            assert [report.original_filename for report in older_reports] == [
                "synthetic-1.png",
                "synthetic-0.png",
            ]
            assert len({report.id for report in reports + older_reports}) == 4
            assert load_session_reports(
                database, user_id=other_user_id, session_id=session_id
            ) == []
            assert load_session_reports(
                database, user_id=owner_id, session_id=other_session_id
            ) == []

            with pytest.raises(ValueError, match="limit must be between"):
                load_session_reports(
                    database, user_id=owner_id, session_id=session_id, limit=51
                )

            database.delete(owner)
            database.delete(other_user)
            database.commit()
    finally:
        engine.dispose()