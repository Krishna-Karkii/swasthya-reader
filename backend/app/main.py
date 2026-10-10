from collections.abc import Generator
from datetime import datetime, timezone
from uuid import UUID, uuid5

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession, Report, User
from app.db.queries import load_message_page, load_recent_messages, load_session_reports
from app.db.session import get_database
from app.schemas import (
    MessageCreate,
    MessageCreateResponse,
    MessageListResponse,
    MessageResponse,
    ReportListResponse,
    ReportResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
)


app = FastAPI(title="Swasthya Reader API", version="0.1.0")
DEMO_USER_ID = uuid5(UUID("00000000-0000-0000-0000-000000000000"), "swasthya-reader-demo")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


def database_dependency() -> Generator[Session, None, None]:
    yield from get_database()


def get_demo_user(database: Session) -> User:
    user = database.get(User, DEMO_USER_ID)
    if user is None:
        user = User(id=DEMO_USER_ID)
        database.add(user)
        database.commit()
        database.refresh(user)
    return user


def get_demo_session(database: Session, session_id: UUID, user_id: UUID) -> ChatSession:
    chat_session = database.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_session


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    database: Session = Depends(database_dependency),
) -> ChatSession:
    user = get_demo_user(database)
    chat_session = ChatSession(user_id=user.id, title=payload.title)
    database.add(chat_session)
    database.commit()
    database.refresh(chat_session)
    return chat_session


@app.get("/api/v1/sessions", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    database: Session = Depends(database_dependency),
) -> SessionListResponse:
    user = get_demo_user(database)
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .limit(limit)
    )
    sessions = list(database.scalars(statement).all())
    return SessionListResponse(items=sessions)


@app.get("/api/v1/sessions/{session_id}/messages", response_model=MessageListResponse)
def list_messages(
    session_id: UUID,
    limit: int = Query(default=20, ge=1, le=50),
    database: Session = Depends(database_dependency),
) -> MessageListResponse:
    user = get_demo_user(database)
    get_demo_session(database, session_id, user.id)
    messages = load_message_page(database, user_id=user.id, session_id=session_id, limit=limit)
    return MessageListResponse(session_id=session_id, items=messages)


@app.post(
    "/api/v1/sessions/{session_id}/messages",
    response_model=MessageCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    session_id: UUID,
    payload: MessageCreate,
    database: Session = Depends(database_dependency),
) -> MessageCreateResponse:
    user = get_demo_user(database)
    chat_session = get_demo_session(database, session_id, user.id)

    user_message = ChatMessage(session_id=chat_session.id, role="user", content=payload.content)
    database.add(user_message)
    database.flush()
    recent_messages = load_recent_messages(
        database, user_id=user.id, session_id=chat_session.id, limit=10
    )
    assistant_message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=(
            "This testing assistant can discuss stored session messages, but report analysis "
            "and medical interpretation are not configured yet."
        ),
    )
    database.add(assistant_message)
    chat_session.updated_at = datetime.now(timezone.utc)
    database.commit()
    database.refresh(user_message)
    database.refresh(assistant_message)
    return MessageCreateResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        session_id=chat_session.id,
        memory={"mode": "recent_messages", "messages_used": len(recent_messages)},
    )


@app.post(
    "/api/v1/sessions/{session_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_report(
    session_id: UUID,
    file: UploadFile = File(...),
    database: Session = Depends(database_dependency),
) -> Report:
    user = get_demo_user(database)
    chat_session = get_demo_session(database, session_id, user.id)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG and PNG images are supported")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Report image must be 10 MB or smaller")

    report = Report(
        session_id=chat_session.id,
        status="uploaded",
        mime_type=file.content_type,
        original_filename=file.filename,
    )
    database.add(report)
    chat_session.updated_at = datetime.now(timezone.utc)
    database.commit()
    database.refresh(report)
    return report


@app.get("/api/v1/sessions/{session_id}/reports", response_model=ReportListResponse)
def list_reports(
    session_id: UUID,
    limit: int = Query(default=20, ge=1, le=50),
    database: Session = Depends(database_dependency),
) -> ReportListResponse:
    user = get_demo_user(database)
    get_demo_session(database, session_id, user.id)
    reports = load_session_reports(database, user_id=user.id, session_id=session_id, limit=limit)
    return ReportListResponse(items=reports)
