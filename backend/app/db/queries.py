from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession

MAX_RECENT_MESSAGE_WINDOW = 20
MAX_MESSAGE_PAGE_SIZE = 50


def load_recent_messages(
    database: Session,
    *,
    user_id: UUID,
    session_id: UUID,
    limit: int = 10,
) -> list[ChatMessage]:
    if not 1 <= limit <= MAX_RECENT_MESSAGE_WINDOW:
        raise ValueError(f"limit must be between 1 and {MAX_RECENT_MESSAGE_WINDOW}")

    statement = (
        select(ChatMessage)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
    )
    return list(reversed(database.scalars(statement).all()))


def load_message_page(
    database: Session,
    *,
    user_id: UUID,
    session_id: UUID,
    limit: int = 20,
    before: tuple[datetime, UUID] | None = None,
) -> list[ChatMessage]:
    if not 1 <= limit <= MAX_MESSAGE_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {MAX_MESSAGE_PAGE_SIZE}")

    statement = (
        select(ChatMessage)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    if before is not None:
        before_created_at, before_id = before
        statement = statement.where(
            or_(
                ChatMessage.created_at < before_created_at,
                and_(ChatMessage.created_at == before_created_at, ChatMessage.id < before_id),
            )
        )

    statement = statement.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit)
    return list(reversed(database.scalars(statement).all()))