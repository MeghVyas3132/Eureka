import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from db.base_class import Base


class SalesData(Base):
    __tablename__ = "sales_data"
    __table_args__ = (
        UniqueConstraint("store_id", "sku", "period_start", "period_end", name="uq_sales_store_sku_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    period_start: Mapped[str] = mapped_column(String(20), nullable=False)
    period_end: Mapped[str] = mapped_column(String(20), nullable=False)
    units_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue: Mapped[float] = mapped_column(Float, nullable=False)
    ingestion_method: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    store: Mapped["Store"] = relationship("Store")
