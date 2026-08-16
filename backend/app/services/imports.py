import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analytics import (
    ImportBatch,
    ImportError,
    InventorySnapshot,
    Product,
    SalesFact,
)
from app.models.common import utc_now
from app.schemas.imports import ImportBatchRead, ImportErrorRead, ImportPreview
from app.services.access import require_project_access
from app.services.import_parser import ParsedImport, parse_and_validate

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


def _serialize_value(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_row(row: dict) -> dict[str, str | int | float | None]:
    return {key: _serialize_value(value) for key, value in row.items()}


def batch_to_read(batch: ImportBatch) -> ImportBatchRead:
    return ImportBatchRead(
        id=batch.id,
        department_id=batch.department_id,
        project_id=batch.project_id,
        created_by=batch.created_by,
        kind=batch.kind,
        original_name=batch.original_name,
        sha256=batch.sha256,
        size_bytes=batch.size_bytes,
        mapping=json.loads(batch.mapping_json),
        status=batch.status,
        total_rows=batch.total_rows,
        success_rows=batch.success_rows,
        failed_rows=batch.failed_rows,
        created_at=batch.created_at,
        confirmed_at=batch.confirmed_at,
        completed_at=batch.completed_at,
        error_message=batch.error_message,
    )


def _replace_validation(session: Session, batch: ImportBatch, parsed: ParsedImport) -> ImportBatch:
    batch.mapping_json = json.dumps(parsed.mapping, ensure_ascii=False)
    batch.preview_json = json.dumps(
        [_serialize_row(row) for row in parsed.valid_rows[:20]], ensure_ascii=False
    )
    batch.status = "validated"
    batch.total_rows = parsed.total_rows
    batch.success_rows = len(parsed.valid_rows)
    batch.failed_rows = len({issue.row_number for issue in parsed.issues})
    batch.error_message = None
    batch.errors.clear()
    for issue in parsed.issues:
        batch.errors.append(
            ImportError(
                row_number=issue.row_number,
                field_name=issue.field_name,
                error_code=issue.error_code,
                message=issue.message,
                raw_row_json=json.dumps(issue.raw_row, ensure_ascii=False, default=str),
            )
        )
    session.commit()
    session.refresh(batch)
    return batch


async def create_import_batch(
    session: Session,
    project_id: str,
    user_id: str,
    kind: str,
    upload: UploadFile,
) -> tuple[ImportBatch, list[str]]:
    if kind not in {"sales", "inventory"}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "kind must be sales or inventory")
    project = require_project_access(session, project_id, user_id)
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only CSV and XLSX files are supported")

    settings = get_settings()
    directory = settings.upload_dir / "imports" / project_id
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{uuid4().hex}{suffix}"
    digest = hashlib.sha256()
    size = 0
    limit = settings.max_upload_size_mb * 1024 * 1024

    try:
        with target.open("wb") as destination:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        f"File exceeds {settings.max_upload_size_mb} MB limit",
                    )
                digest.update(chunk)
                destination.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    sha256 = digest.hexdigest()
    duplicate = session.scalar(
        select(ImportBatch).where(ImportBatch.sha256 == sha256, ImportBatch.kind == kind)
    )
    if duplicate:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Duplicate file already exists in batch {duplicate.id}",
        )

    try:
        parsed = parse_and_validate(target, kind)
    except Exception as error:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unable to parse file: {error}"
        ) from error

    batch = ImportBatch(
        department_id=project.department_id,
        project_id=project_id,
        created_by=user_id,
        kind=kind,
        original_name=Path(upload.filename or f"report{suffix}").name,
        storage_path=str(target),
        sha256=sha256,
        size_bytes=size,
    )
    session.add(batch)
    session.flush()
    _replace_validation(session, batch, parsed)
    return batch, parsed.headers


def update_import_mapping(
    session: Session, batch_id: str, user_id: str, mapping: dict[str, str]
) -> ImportBatch:
    batch = require_import_batch(session, batch_id, user_id)
    if batch.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Completed import cannot be remapped")
    parsed = parse_and_validate(Path(batch.storage_path), batch.kind, mapping)
    return _replace_validation(session, batch, parsed)


def require_import_batch(session: Session, batch_id: str, user_id: str) -> ImportBatch:
    batch = session.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Import batch not found")
    require_project_access(session, batch.project_id, user_id)
    return batch


def get_import_preview(session: Session, batch_id: str, user_id: str) -> ImportPreview:
    batch = require_import_batch(session, batch_id, user_id)
    return ImportPreview(
        batch=batch_to_read(batch),
        rows=json.loads(batch.preview_json),
        errors=[
            ImportErrorRead(
                row_number=error.row_number,
                field_name=error.field_name,
                error_code=error.error_code,
                message=error.message,
            )
            for error in batch.errors[:50]
        ],
    )


def _get_or_create_product(
    session: Session, row: dict, cache: dict[tuple[str, str, str], Product]
) -> Product:
    key = (row["sku"], row["site"], row["platform"])
    if key in cache:
        return cache[key]
    product = session.scalar(
        select(Product).where(
            Product.sku == key[0], Product.site == key[1], Product.platform == key[2]
        )
    )
    if not product:
        unit_cost = Decimal("0")
        if row.get("units_sold"):
            unit_cost = row["cost"] / row["units_sold"]
        product = Product(
            sku=row["sku"],
            name=row["product_name"],
            category=row["category"],
            site=row["site"],
            platform=row["platform"],
            unit_cost=unit_cost,
        )
        session.add(product)
        session.flush()
    cache[key] = product
    return product


def confirm_import_batch(session: Session, batch_id: str, user_id: str) -> ImportBatch:
    batch = require_import_batch(session, batch_id, user_id)
    if batch.status == "completed":
        return batch
    parsed = parse_and_validate(
        Path(batch.storage_path), batch.kind, json.loads(batch.mapping_json)
    )
    if not parsed.valid_rows:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No valid rows to import")

    try:
        batch.status = "importing"
        batch.confirmed_at = utc_now()
        products: dict[tuple[str, str, str], Product] = {}
        for row in parsed.valid_rows:
            product = _get_or_create_product(session, row, products)
            if batch.kind == "sales":
                session.add(
                    SalesFact(
                        product_id=product.id,
                        sale_date=row["sale_date"],
                        units_sold=row["units_sold"],
                        revenue=row["revenue"],
                        cost=row["cost"],
                        refund_units=row["refund_units"],
                        import_batch_id=batch.id,
                        source_row_number=row["source_row_number"],
                    )
                )
            else:
                session.add(
                    InventorySnapshot(
                        product_id=product.id,
                        snapshot_date=row["snapshot_date"],
                        on_hand=row["on_hand"],
                        reserved=row["reserved"],
                        inbound=row["inbound"],
                        import_batch_id=batch.id,
                    )
                )
        batch.status = "completed"
        batch.completed_at = utc_now()
        batch.success_rows = len(parsed.valid_rows)
        session.commit()
        session.refresh(batch)
        return batch
    except SQLAlchemyError as error:
        session.rollback()
        failed_batch = session.get(ImportBatch, batch_id)
        if failed_batch:
            failed_batch.status = "failed"
            failed_batch.error_message = str(error.__class__.__name__)
            session.commit()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Import transaction rolled back"
        ) from error
