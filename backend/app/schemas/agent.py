from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.communication import MessageRead


class AgentRunCreate(BaseModel):
    user_id: str
    content: str = Field(min_length=1, max_length=20_000)


class ToolCallRead(BaseModel):
    id: str
    tool_name: str
    input: dict
    output_summary: dict | None
    status: str
    duration_ms: int
    error_message: str | None
    created_at: datetime


class AgentRunRead(BaseModel):
    id: str
    department_id: str
    user_id: str
    project_id: str
    conversation_id: str
    provider: str
    model_name: str
    status: str
    input_summary: str
    output_summary: str | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    assistant_message: MessageRead | None = None
    tool_calls: list[ToolCallRead]
