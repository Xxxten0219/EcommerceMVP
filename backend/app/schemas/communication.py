from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    user_id: str
    title: str = Field(default="新聊天", min_length=1, max_length=120)


class ConversationRename(BaseModel):
    user_id: str
    title: str = Field(min_length=1, max_length=120)


class ConversationRead(BaseModel):
    id: str
    project_id: str
    created_by: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    user_id: str
    content: str = Field(min_length=1, max_length=20_000)


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    user_id: str | None
    role: str
    content: str
    metadata_json: str
    created_at: datetime


class ContextMessage(BaseModel):
    role: str
    content: str
    created_at: datetime


class ContextSnapshot(BaseModel):
    project_id: str
    conversation_id: str
    project_summary: str
    structured_scope: dict[str, str]
    recent_messages: list[ContextMessage]
