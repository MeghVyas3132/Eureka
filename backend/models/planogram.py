import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from db.base_class import Base


class Planogram(Base):
    __tablename__ = "planograms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Auto-Generated Planogram")
    generation_level: Mapped[str] = mapped_column(String(50), nullable=False, default="store")
    generation_method: Mapped[str] = mapped_column(String(50), nullable=False, default="auto")
    shelf_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    shelf_width_cm: Mapped[float] = mapped_column(Float, nullable=False, default=180.0)
    shelf_height_cm: Mapped[float] = mapped_column(Float, nullable=False, default=200.0)
    planogram_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_auto_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    store: Mapped["Store"] = relationship("Store", back_populates="planograms")
    versions: Mapped[list["PlanogramVersion"]] = relationship(
        "PlanogramVersion",
        back_populates="planogram",
        cascade="all, delete-orphan",
        order_by="PlanogramVersion.version_number.desc()",
    )
