from datetime import datetime

from pydantic import BaseModel, Field


class ImportMappingUpdate(BaseModel):
    user_id: str
    mapping: dict[str, str]


class ImportConfirm(BaseModel):
    user_id: str


class ImportErrorRead(BaseModel):
    row_number: int
    field_name: str | None
    error_code: str
    message: str


class ImportBatchRead(BaseModel):
    id: str
    department_id: str
    project_id: str
    created_by: str
    kind: str
    original_name: str
    sha256: str
    size_bytes: int
    mapping: dict[str, str]
    status: str
    total_rows: int
    success_rows: int
    failed_rows: int
    created_at: datetime
    confirmed_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class ImportPreview(BaseModel):
    batch: ImportBatchRead
    rows: list[dict[str, str | int | float | None]]
    errors: list[ImportErrorRead]


class ImportUploadResponse(ImportPreview):
    detected_headers: list[str] = Field(default_factory=list)
