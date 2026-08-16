from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.image import (
    ImageAssetRead,
    ImageEditCreate,
    ImageRetry,
    ImageVersionRead,
)
from app.services.images import (
    asset_to_read,
    create_image_version,
    list_image_assets,
    list_image_versions,
    require_image_attachment,
    retry_image_version,
    upload_image_asset,
    version_to_read,
)

router = APIRouter(tags=["images"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/image-assets", response_model=ImageAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_source_image(
    project_id: Annotated[str, Form()],
    conversation_id: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    session: SessionDependency,
) -> ImageAssetRead:
    asset = await upload_image_asset(session, project_id, conversation_id, user_id, file)
    return asset_to_read(asset)


@router.post(
    "/image-versions", response_model=ImageVersionRead, status_code=status.HTTP_201_CREATED
)
def edit_image(payload: ImageEditCreate, session: SessionDependency) -> ImageVersionRead:
    return version_to_read(create_image_version(session, payload))


@router.get("/conversations/{conversation_id}/image-assets", response_model=list[ImageAssetRead])
def image_assets(
    conversation_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> list[ImageAssetRead]:
    return [asset_to_read(item) for item in list_image_assets(session, conversation_id, user_id)]


@router.get(
    "/conversations/{conversation_id}/image-versions",
    response_model=list[ImageVersionRead],
)
def image_versions(
    conversation_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
) -> list[ImageVersionRead]:
    return [
        version_to_read(item) for item in list_image_versions(session, conversation_id, user_id)
    ]


@router.post("/image-versions/{version_id}/retry", response_model=ImageVersionRead)
def retry_image(
    version_id: str, payload: ImageRetry, session: SessionDependency
) -> ImageVersionRead:
    return version_to_read(retry_image_version(session, version_id, payload.user_id))


@router.get("/attachments/{attachment_id}/content", response_class=FileResponse)
def image_content(
    attachment_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
    download: Annotated[bool, Query()] = False,
) -> FileResponse:
    attachment = require_image_attachment(session, attachment_id, user_id)
    return FileResponse(
        Path(attachment.storage_path),
        media_type=attachment.mime_type,
        filename=attachment.original_name if download else None,
    )
