import csv
import io
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.imports import (
    ImportBatchRead,
    ImportConfirm,
    ImportMappingUpdate,
    ImportPreview,
    ImportUploadResponse,
)
from app.services.imports import (
    batch_to_read,
    confirm_import_batch,
    create_import_batch,
    get_import_preview,
    require_import_batch,
    update_import_mapping,
)

router = APIRouter(tags=["imports"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/imports", response_model=ImportUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_import(
    project_id: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    kind: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    session: SessionDependency,
) -> ImportUploadResponse:
    batch, headers = await create_import_batch(session, project_id, user_id, kind, file)
    preview = get_import_preview(session, batch.id, user_id)
    return ImportUploadResponse(**preview.model_dump(), detected_headers=headers)


@router.post("/imports/{batch_id}/mapping", response_model=ImportPreview)
def update_mapping(
    batch_id: str, payload: ImportMappingUpdate, session: SessionDependency
) -> ImportPreview:
    update_import_mapping(session, batch_id, payload.user_id, payload.mapping)
    return get_import_preview(session, batch_id, payload.user_id)


@router.get("/imports/{batch_id}/preview", response_model=ImportPreview)
def preview(
    batch_id: str, user_id: Annotated[str, Query()], session: SessionDependency
) -> ImportPreview:
    return get_import_preview(session, batch_id, user_id)


@router.post("/imports/{batch_id}/confirm", response_model=ImportBatchRead)
def confirm(batch_id: str, payload: ImportConfirm, session: SessionDependency) -> ImportBatchRead:
    return batch_to_read(confirm_import_batch(session, batch_id, payload.user_id))


@router.get("/imports/{batch_id}", response_model=ImportBatchRead)
def batch_status(
    batch_id: str, user_id: Annotated[str, Query()], session: SessionDependency
) -> ImportBatchRead:
    return batch_to_read(require_import_batch(session, batch_id, user_id))


@router.get("/imports/{batch_id}/errors.csv")
def export_errors(
    batch_id: str, user_id: Annotated[str, Query()], session: SessionDependency
) -> StreamingResponse:
    batch = require_import_batch(session, batch_id, user_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["row_number", "field_name", "error_code", "message", "raw_row"])
    for error in batch.errors:
        writer.writerow(
            [
                error.row_number,
                error.field_name or "",
                error.error_code,
                error.message,
                json.loads(error.raw_row_json),
            ]
        )
    return StreamingResponse(
        iter([buffer.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="import-{batch_id}-errors.csv"'},
    )
