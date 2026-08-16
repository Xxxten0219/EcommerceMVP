from datetime import datetime

from pydantic import BaseModel, Field


class ImageAssetRead(BaseModel):
    id: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime


class ImageEditCreate(BaseModel):
    user_id: str
    conversation_id: str
    source_attachment_id: str
    parent_version_id: str | None = None
    prompt: str = Field(min_length=1, max_length=4000)


class ImageRetry(BaseModel):
    user_id: str


class ImageVersionRead(BaseModel):
    id: str
    project_id: str
    conversation_id: str
    source_attachment_id: str
    parent_version_id: str | None
    output_attachment_id: str | None
    prompt: str
    provider: str
    model_name: str
    status: str
    retry_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
