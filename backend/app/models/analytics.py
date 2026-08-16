from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import new_uuid, utc_now


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("sku", "site", "platform", name="uq_products_scope_sku"),
        Index("ix_products_scope_category", "site", "platform", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sku: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    site: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SalesFact(Base):
    __tablename__ = "sales_facts"
    __table_args__ = (
        UniqueConstraint("import_batch_id", "source_row_number", name="uq_sales_batch_row"),
        Index("ix_sales_product_date", "product_id", "sale_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    units_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    refund_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    import_batch_id: Mapped[str | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    __table_args__ = (Index("ix_inventory_product_date", "product_id", "snapshot_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inbound: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    import_batch_id: Mapped[str | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="RESTRICT"), nullable=True, index=True
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"
    __table_args__ = (
        UniqueConstraint("sha256", "kind", name="uq_import_batch_hash_kind"),
        Index("ix_import_project_created", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mapping_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    preview_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="uploaded")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    errors: Mapped[list["ImportError"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class ImportError(Base):
    __tablename__ = "import_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_row_json: Mapped[str] = mapped_column(Text, nullable=False)

    batch: Mapped[ImportBatch] = relationship(back_populates="errors")
