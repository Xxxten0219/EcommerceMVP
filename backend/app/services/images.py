import hashlib
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.communication import Attachment, Message
from app.models.image import ImageVersion
from app.providers.image import get_image_provider
from app.schemas.image import ImageAssetRead, ImageEditCreate, ImageVersionRead
from app.services.access import require_project_access
from app.services.communication import require_conversation_access

ALLOWED_IMAGE_FORMATS = {
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "WEBP": (".webp", "image/webp"),
}


def asset_to_read(asset: Attachment) -> ImageAssetRead:
    return ImageAssetRead(
        id=asset.id,
        original_name=asset.original_name,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        sha256=asset.sha256,
        created_at=asset.created_at,
    )


def version_to_read(version: ImageVersion) -> ImageVersionRead:
    return ImageVersionRead(
        id=version.id,
        project_id=version.project_id,
        conversation_id=version.conversation_id,
        source_attachment_id=version.source_attachment_id,
        parent_version_id=version.parent_version_id,
        output_attachment_id=version.output_attachment_id,
        prompt=version.prompt,
        provider=version.provider,
        model_name=version.model_name,
        status=version.status,
        retry_count=version.retry_count,
        error_message=version.error_message,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _inspect_image(content: bytes) -> tuple[str, str]:
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
            image_format = image.format or ""
            width, height = image.size
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Uploaded file is not a valid image"
        ) from error
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only JPEG, PNG and WEBP images are supported"
        )
    if width * height > 36_000_000:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image dimensions are too large")
    return ALLOWED_IMAGE_FORMATS[image_format]


def _require_artwork_project(session: Session, project_id: str, user_id: str):
    project = require_project_access(session, project_id, user_id)
    if project.department.code != "artwork":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image workflow requires artwork project")
    return project


async def upload_image_asset(
    session: Session,
    project_id: str,
    conversation_id: str,
    user_id: str,
    upload: UploadFile,
) -> Attachment:
    project = _require_artwork_project(session, project_id, user_id)
    conversation = require_conversation_access(session, conversation_id, user_id)
    if conversation.project_id != project.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Conversation does not belong to project")
    settings = get_settings()
    limit = settings.max_upload_size_mb * 1024 * 1024
    content = await upload.read(limit + 1)
    await upload.close()
    if len(content) > limit:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.max_upload_size_mb} MB limit",
        )
    suffix, mime_type = _inspect_image(content)
    directory = settings.upload_dir / "images" / project.id
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{uuid4().hex}{suffix}"
    target.write_bytes(content)
    asset = Attachment(
        department_id=project.department_id,
        user_id=user_id,
        project_id=project.id,
        conversation_id=conversation.id,
        kind="source_image",
        original_name=Path(upload.filename or f"source{suffix}").name,
        storage_path=str(target),
        mime_type=mime_type,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    message = Message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=f"[上传商品原图] {asset.original_name}",
        metadata_json="{}",
    )
    try:
        session.add_all([asset, message])
        session.flush()
        asset.message_id = message.id
        message.metadata_json = json.dumps(
            {"attachment_ids": [asset.id], "kind": "source_image"}, ensure_ascii=False
        )
        session.commit()
        session.refresh(asset)
        return asset
    except Exception:
        session.rollback()
        target.unlink(missing_ok=True)
        raise


def _require_source(session: Session, attachment_id: str, project_id: str) -> Attachment:
    attachment = session.get(Attachment, attachment_id)
    if not attachment or attachment.project_id != project_id or attachment.kind != "source_image":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source image not found in project")
    return attachment


def _input_attachment(session: Session, version: ImageVersion) -> Attachment:
    if version.parent_version_id:
        parent = session.get(ImageVersion, version.parent_version_id)
        if (
            not parent
            or parent.project_id != version.project_id
            or parent.source_attachment_id != version.source_attachment_id
            or parent.status != "completed"
            or not parent.output_attachment_id
        ):
            raise HTTPException(status.HTTP_409_CONFLICT, "Parent image version is not usable")
        attachment = session.get(Attachment, parent.output_attachment_id)
    else:
        attachment = session.get(Attachment, version.source_attachment_id)
    if not attachment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Input image attachment not found")
    return attachment


def _execute_image_version(session: Session, version: ImageVersion) -> ImageVersion:
    settings = get_settings()
    provider = get_image_provider()
    input_asset = _input_attachment(session, version)
    output_path = settings.generated_dir / "images" / version.project_id / f"{version.id}.png"
    version.provider = provider.name
    version.model_name = provider.model_name
    version.status = "running"
    version.retry_count += 1
    version.error_message = None
    session.commit()
    try:
        provider.edit(
            Path(input_asset.storage_path), output_path, version.prompt, version.retry_count
        )
        content = output_path.read_bytes()
        _inspect_image(content)
        assistant = Message(
            conversation_id=version.conversation_id,
            role="assistant",
            content=f"图片编辑已完成，已保存为版本 {version.id[:8]}。",
            metadata_json="{}",
        )
        output_asset = Attachment(
            department_id=version.department_id,
            user_id=version.user_id,
            project_id=version.project_id,
            conversation_id=version.conversation_id,
            kind="generated_image",
            original_name=f"edited-{version.id[:8]}.png",
            storage_path=str(output_path),
            mime_type="image/png",
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        session.add_all([assistant, output_asset])
        session.flush()
        output_asset.message_id = assistant.id
        assistant.metadata_json = json.dumps(
            {
                "attachment_ids": [output_asset.id],
                "image_version_id": version.id,
            },
            ensure_ascii=False,
        )
        version.output_attachment_id = output_asset.id
        version.status = "completed"
        session.commit()
    except Exception as error:
        session.rollback()
        output_path.unlink(missing_ok=True)
        failed = session.get(ImageVersion, version.id)
        if not failed:
            raise
        failed.status = "failed"
        failed.error_message = str(error)[:1000]
        session.add(
            Message(
                conversation_id=failed.conversation_id,
                role="assistant",
                content=f"图片编辑失败，请保留当前请求后重试：{failed.error_message}",
                metadata_json=json.dumps({"image_version_id": failed.id}),
            )
        )
        session.commit()
        version = failed
    session.refresh(version)
    return version


def create_image_version(session: Session, payload: ImageEditCreate) -> ImageVersion:
    conversation = require_conversation_access(session, payload.conversation_id, payload.user_id)
    project = _require_artwork_project(session, conversation.project_id, payload.user_id)
    _require_source(session, payload.source_attachment_id, project.id)
    if payload.parent_version_id:
        parent = session.get(ImageVersion, payload.parent_version_id)
        if (
            not parent
            or parent.conversation_id != conversation.id
            or parent.source_attachment_id != payload.source_attachment_id
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid parent image version")
    provider = get_image_provider()
    version = ImageVersion(
        department_id=project.department_id,
        user_id=payload.user_id,
        project_id=project.id,
        conversation_id=conversation.id,
        source_attachment_id=payload.source_attachment_id,
        parent_version_id=payload.parent_version_id,
        prompt=payload.prompt,
        provider=provider.name,
        model_name=provider.model_name,
    )
    message = Message(
        conversation_id=conversation.id,
        user_id=payload.user_id,
        role="user",
        content=payload.prompt,
        metadata_json=json.dumps(
            {
                "attachment_ids": [payload.source_attachment_id],
                "parent_version_id": payload.parent_version_id,
            },
            ensure_ascii=False,
        ),
    )
    session.add_all([version, message])
    session.commit()
    session.refresh(version)
    return _execute_image_version(session, version)


def retry_image_version(session: Session, version_id: str, user_id: str) -> ImageVersion:
    version = session.get(ImageVersion, version_id)
    if not version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image version not found")
    require_project_access(session, version.project_id, user_id)
    if version.status != "failed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only failed versions can be retried")
    return _execute_image_version(session, version)


def list_image_versions(session: Session, conversation_id: str, user_id: str) -> list[ImageVersion]:
    require_conversation_access(session, conversation_id, user_id)
    return list(
        session.scalars(
            select(ImageVersion)
            .where(ImageVersion.conversation_id == conversation_id)
            .order_by(ImageVersion.created_at, ImageVersion.id)
        ).all()
    )


def list_image_assets(session: Session, conversation_id: str, user_id: str) -> list[Attachment]:
    require_conversation_access(session, conversation_id, user_id)
    return list(
        session.scalars(
            select(Attachment)
            .where(
                Attachment.conversation_id == conversation_id,
                Attachment.kind == "source_image",
            )
            .order_by(Attachment.created_at, Attachment.id)
        ).all()
    )


def require_image_attachment(session: Session, attachment_id: str, user_id: str) -> Attachment:
    attachment = session.get(Attachment, attachment_id)
    if not attachment or attachment.kind not in {"source_image", "generated_image"}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image attachment not found")
    require_project_access(session, attachment.project_id, user_id)
    path = Path(attachment.storage_path).resolve()
    settings = get_settings()
    allowed_roots = [settings.upload_dir.resolve(), settings.generated_dir.resolve()]
    if not any(path.is_relative_to(root) for root in allowed_roots) or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image file is unavailable")
    return attachment
