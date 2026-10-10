from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=160)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    next_cursor: str | None = None


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="en", min_length=2, max_length=8)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    session_id: UUID
    items: list[MessageResponse]
    next_cursor: str | None = None


class MessageCreateResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    session_id: UUID
    memory: dict[str, Any]


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    status: str
    original_filename: str | None
    mime_type: str
    extraction_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
